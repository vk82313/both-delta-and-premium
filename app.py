import websocket
import json
import requests
import os
from datetime import datetime, timedelta, timezone
from time import sleep
from flask import Flask, request, render_template_string, redirect
import threading
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import time as time_module

# Initialize Flask app
app = Flask(__name__)

# -------------------------------
# Configuration & Global State
# -------------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Global thresholds for arbitrage system - UPDATED DEFAULT VALUES
DELTA_THRESHOLD = {"ETH": 0.05, "BTC": 0.5}
ALERT_COOLDOWN = 60
PROCESS_INTERVAL = 2
EXPIRY_CHECK_INTERVAL = 60
BTC_FETCH_INTERVAL = 1

# -------------------------------
# System 2: Option Alert Configuration
# -------------------------------
@dataclass
class AlertConfig:
    strike: float = 0
    premium: float = 0
    is_monitoring: bool = False
    last_updated: str = ""
    active_expiry: str = ""

alert_configs = {
    'btc_call': AlertConfig(),
    'btc_put': AlertConfig(),
    'eth_call': AlertConfig(),
    'eth_put': AlertConfig()
}

previous_configs = {}
new_system_active = False
last_check_time = None

# -------------------------------
# System 3: Dual Condition Spike Detection Configuration
# -------------------------------
@dataclass
class SpikeConfig:
    enabled_spike: bool = False
    min_spike_percent: float = 100.0
    spike_min_premium: float = 1.0
    enabled_spread: bool = False
    min_spread_percent: float = 100.0
    spread_min_premium: float = 0.5
    monitor_eth: bool = True
    monitor_btc: bool = True
    monitor_calls: bool = True
    monitor_puts: bool = True

spike_config = SpikeConfig()
price_history = {}
last_spike_alert = {}
last_spread_alert = {}
SPIKE_COOLDOWN_SECONDS = 120

# -------------------------------
# System 4: Exact Premium Match Detection Configuration
# -------------------------------
@dataclass
class PremiumMatchConfig:
    enabled: bool = False
    cooldown_seconds: int = 60
    btc_min_premium: float = 0.0
    eth_min_premium: float = 0.0

premium_match_config = PremiumMatchConfig()
last_premium_match_alert = {}
system4_active = False
system4_btc_match_count = 0
system4_eth_match_count = 0
system4_last_alert = None
system4_start_time = None

# -------------------------------
# System 5: Premium Tracker Configuration (NO COOLDOWN)
# -------------------------------
@dataclass
class PremiumTrackerConfig:
    active: bool = False
    strike: float = 0
    last_ask_price: float = 0.0

premium_tracker_configs = {
    'btc_call': PremiumTrackerConfig(),
    'btc_put': PremiumTrackerConfig(),
    'eth_call': PremiumTrackerConfig(),
    'eth_put': PremiumTrackerConfig()
}

system5_alert_counts = {
    'btc_call': 0,
    'btc_put': 0,
    'eth_call': 0,
    'eth_put': 0
}

# -------------------------------
# Utility Functions
# -------------------------------
def get_ist_time():
    utc_now = datetime.now(timezone.utc)
    ist_offset = timedelta(hours=5, minutes=30)
    ist_time = utc_now + ist_offset
    return ist_time.strftime("%H:%M:%S")

def get_current_expiry():
    utc_now = datetime.now(timezone.utc)
    ist_now = utc_now + timedelta(hours=5, minutes=30)
    return ist_now.strftime("%d%m%y")

def format_expiry_display(expiry_code):
    try:
        day = expiry_code[:2]
        month = expiry_code[2:4]
        year = "20" + expiry_code[4:6]
        month_names = {
            '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr',
            '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Aug',
            '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'
        }
        return f"{day} {month_names[month]} {year}"
    except:
        return expiry_code

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"[{datetime.now()}] 📱 Telegram not configured: {message}")
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        resp = requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID, 
            "text": message, 
            "parse_mode": "Markdown"
        })
        if resp.status_code == 200:
            print(f"[{datetime.now()}] 📱 Telegram alert sent")
        else:
            print(f"[{datetime.now()}] ❌ Telegram error {resp.status_code}")
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Telegram error: {e}")

def send_config_update_telegram(config_id: str, old_config: Dict, new_config: Dict):
    config_names = {
        'btc_call': 'BTC CALL',
        'btc_put': 'BTC PUT',
        'eth_call': 'ETH CALL',
        'eth_put': 'ETH PUT'
    }
    asset_type = config_names.get(config_id, config_id)
    changes = []
    
    if old_config.get('strike', 0) != new_config['strike']:
        changes.append(f"• Strike: {old_config.get('strike', 'Not set')} → {new_config['strike']}")
    if old_config.get('premium', 0) != new_config['premium']:
        changes.append(f"• Premium: ${old_config.get('premium', 0):.2f} → ${new_config['premium']:.2f}")
    if old_config.get('is_monitoring', False) != new_config['is_monitoring']:
        status = "✅ MONITORING" if new_config['is_monitoring'] else "⏸️ NOT MONITORING"
        changes.append(f"• Status: {status}")
    
    if not changes:
        return
        
    message = f"""
⚙️ **ALERT CONFIGURATION UPDATED**

**{asset_type} ALERT**

**Changes:**
{"\n".join(changes)}

**New Configuration:**
• Strike: {new_config['strike']}
• Premium: ${new_config['premium']:.2f}
• Monitoring: {'✅ ACTIVE' if new_config['is_monitoring'] else '⏸️ INACTIVE'}
• Expiry: {new_config.get('active_expiry', 'Current')}

**Updated:** {get_ist_time()}
"""
    send_telegram(message)

def send_alert_triggered_telegram(alert_data: Dict):
    message = f"""
🚨 **{alert_data['asset']} {alert_data['type'].upper()} ALERT TRIGGERED!**

**Condition Met:**
• Looking for: Strike {'>' if alert_data['type'] == 'call' else '<'} {alert_data['config_strike']}
• Bid Price ≥ ${alert_data['threshold']:.2f}

**Found:**
• Strike Price: {alert_data['trigger_strike']}
• Current Bid: ${alert_data['bid_price']:.2f}
• Condition: ${alert_data['bid_price']:.2f} ≥ ${alert_data['threshold']:.2f} ✅

**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    send_telegram(message)

def send_spike_alert_telegram(symbol: str, current_price: float, historical_avg: float, spike_percent: float):
    parts = symbol.split('-')
    asset = "BTC" if "BTC" in symbol else "ETH"
    option_type = "CALL" if parts[0] == "C" else "PUT"
    strike = parts[2] if len(parts) > 2 else "Unknown"
    
    message = f"""
🚨 **PREMIUM SPIKE DETECTED!**

**{asset} {strike} {option_type}**
**Time:** {get_ist_time()}

**Price History:**
• Previous average: ${historical_avg:.2f}
• Current bid: ${current_price:.2f}
• Spike: +{spike_percent:.1f}%

**Alert:** Premium DOUBLED instantly!
"""
    send_telegram(message)

def send_spread_alert_telegram(symbol: str, bid_price: float, ask_price: float, spread_percent: float):
    parts = symbol.split('-')
    asset = "BTC" if "BTC" in symbol else "ETH"
    option_type = "CALL" if parts[0] == "C" else "PUT"
    strike = parts[2] if len(parts) > 2 else "Unknown"
    
    message = f"""
🚨 **BID-ASK SPREAD ALERT!**

**{asset} {strike} {option_type}**
**Time:** {get_ist_time()}

**Current Prices:**
• Bid: ${bid_price:.2f}
• Ask: ${ask_price:.2f}
• Spread: {spread_percent:.1f}%

**Alert:** Spread is {spread_percent:.1f}% (Bid: ${bid_price:.2f}, Ask: ${ask_price:.2f})
"""
    send_telegram(message)

def send_system5_alert_telegram(asset: str, option_type: str, strike: float, old_ask: float, new_ask: float):
    change = new_ask - old_ask
    change_percent = (change / old_ask) * 100 if old_ask > 0 else 0
    direction = "📈" if change > 0 else "📉"
    sign = "+" if change > 0 else ""
    
    message = f"""
🔔 **PREMIUM CHANGE ALERT**

📊 **{asset} {strike} {option_type.upper()}**
💰 Ask Price: ${old_ask:.2f} → ${new_ask:.2f}
{direction} Change: {sign}${change:.2f} ({sign}{change_percent:.2f}%)
⏰ Time: {get_ist_time()}

⚡ **Alert: Immediate change detected!**
"""
    send_telegram(message)

# -------------------------------
# System 4: Premium Match Functions
# -------------------------------
def send_premium_match_telegram(asset: str, option_type: str, 
                                strike_ask: int, strike_bid: int,
                                ask_price: float, bid_price: float, 
                                btc_filter: float, eth_filter: float):
    global system4_btc_match_count, system4_eth_match_count, system4_last_alert
    
    if asset == "BTC":
        system4_btc_match_count += 1
        filter_passed = "PASSED" if ask_price >= btc_filter else "FAILED"
    else:
        system4_eth_match_count += 1
        filter_passed = "PASSED" if ask_price >= eth_filter else "FAILED"
    
    system4_last_alert = get_ist_time()
    
    message = f"""
🎯 **SYSTEM 4: EXACT PREMIUM MATCH DETECTED!**

**{asset} {option_type.upper()} OPTIONS**

**Match Found:**
• Strike {strike_ask} Ask: ${ask_price:.2f}
• Strike {strike_bid} Bid: ${bid_price:.2f}
• **Match: ${ask_price:.2f} = ${bid_price:.2f}** ✅

💰 **Premium Filters:**
• BTC Filter: ≥ ${btc_filter:.2f}
• ETH Filter: ≥ ${eth_filter:.2f}
• This Match: ${ask_price:.2f} ({filter_passed})

**Time:** {get_ist_time()}
"""
    send_telegram(message)

def check_premium_matches_eth(eth_bot):
    global last_premium_match_alert, system4_active, premium_match_config
    if not system4_active or not premium_match_config.enabled:
        return
    
    strikes_data = {}
    for symbol, price_data in eth_bot.options_prices.items():
        if 'ETH' not in symbol:
            continue
        symbol_expiry = eth_bot.extract_expiry_from_symbol(symbol)
        if symbol_expiry != eth_bot.active_expiry:
            continue
        strike = eth_bot.extract_strike(symbol)
        if strike == 0 or price_data['bid'] <= 0 or price_data['ask'] <= 0:
            continue
        if 'C-' in symbol:
            option_type = 'call'
        elif 'P-' in symbol:
            option_type = 'put'
        else:
            continue
        if strike not in strikes_data:
            strikes_data[strike] = {'call': {'bid': 0, 'ask': 0, 'symbol': ''}, 
                                    'put': {'bid': 0, 'ask': 0, 'symbol': ''}}
        if option_type == 'call':
            strikes_data[strike]['call']['bid'] = price_data['bid']
            strikes_data[strike]['call']['ask'] = price_data['ask']
            strikes_data[strike]['call']['symbol'] = symbol
        else:
            strikes_data[strike]['put']['bid'] = price_data['bid']
            strikes_data[strike]['put']['ask'] = price_data['ask']
            strikes_data[strike]['put']['symbol'] = symbol
    
    sorted_strikes = sorted(strikes_data.keys())
    if len(sorted_strikes) < 2:
        return
    
    for i in range(len(sorted_strikes)):
        for j in range(i + 1, len(sorted_strikes)):
            strike_lower = sorted_strikes[i]
            strike_higher = sorted_strikes[j]
            
            lower_ask = strikes_data[strike_lower]['call']['ask']
            higher_bid = strikes_data[strike_higher]['call']['bid']
            if lower_ask > 0 and higher_bid > 0 and lower_ask == higher_bid:
                if lower_ask >= premium_match_config.eth_min_premium:
                    alert_key = f"ETH_CALL_{strike_lower}_{strike_higher}"
                    now = datetime.now().timestamp()
                    last_alert = last_premium_match_alert.get(alert_key, 0)
                    if now - last_alert >= premium_match_config.cooldown_seconds:
                        last_premium_match_alert[alert_key] = now
                        send_premium_match_telegram('ETH', 'call', strike_lower, strike_higher,
                                                   lower_ask, higher_bid,
                                                   premium_match_config.btc_min_premium,
                                                   premium_match_config.eth_min_premium)
            
            higher_ask = strikes_data[strike_higher]['put']['ask']
            lower_bid = strikes_data[strike_lower]['put']['bid']
            if higher_ask > 0 and lower_bid > 0 and higher_ask == lower_bid:
                if higher_ask >= premium_match_config.eth_min_premium:
                    alert_key = f"ETH_PUT_{strike_higher}_{strike_lower}"
                    now = datetime.now().timestamp()
                    last_alert = last_premium_match_alert.get(alert_key, 0)
                    if now - last_alert >= premium_match_config.cooldown_seconds:
                        last_premium_match_alert[alert_key] = now
                        send_premium_match_telegram('ETH', 'put', strike_higher, strike_lower,
                                                   higher_ask, lower_bid,
                                                   premium_match_config.btc_min_premium,
                                                   premium_match_config.eth_min_premium)

def check_premium_matches_btc(btc_bot):
    global last_premium_match_alert, system4_active, premium_match_config
    if not system4_active or not premium_match_config.enabled:
        return
    
    strikes_data = {}
    for symbol, price_data in btc_bot.options_prices.items():
        if 'BTC' not in symbol:
            continue
        strike = btc_bot.extract_strike(symbol)
        if strike == 0 or price_data['bid'] <= 0 or price_data['ask'] <= 0:
            continue
        if symbol.startswith('C-'):
            option_type = 'call'
        elif symbol.startswith('P-'):
            option_type = 'put'
        else:
            continue
        if strike not in strikes_data:
            strikes_data[strike] = {'call': {'bid': 0, 'ask': 0, 'symbol': ''}, 
                                    'put': {'bid': 0, 'ask': 0, 'symbol': ''}}
        if option_type == 'call':
            strikes_data[strike]['call']['bid'] = price_data['bid']
            strikes_data[strike]['call']['ask'] = price_data['ask']
            strikes_data[strike]['call']['symbol'] = symbol
        else:
            strikes_data[strike]['put']['bid'] = price_data['bid']
            strikes_data[strike]['put']['ask'] = price_data['ask']
            strikes_data[strike]['put']['symbol'] = symbol
    
    sorted_strikes = sorted(strikes_data.keys())
    if len(sorted_strikes) < 2:
        return
    
    for i in range(len(sorted_strikes)):
        for j in range(i + 1, len(sorted_strikes)):
            strike_lower = sorted_strikes[i]
            strike_higher = sorted_strikes[j]
            
            lower_ask = strikes_data[strike_lower]['call']['ask']
            higher_bid = strikes_data[strike_higher]['call']['bid']
            if lower_ask > 0 and higher_bid > 0 and lower_ask == higher_bid:
                if lower_ask >= premium_match_config.btc_min_premium:
                    alert_key = f"BTC_CALL_{strike_lower}_{strike_higher}"
                    now = datetime.now().timestamp()
                    last_alert = last_premium_match_alert.get(alert_key, 0)
                    if now - last_alert >= premium_match_config.cooldown_seconds:
                        last_premium_match_alert[alert_key] = now
                        send_premium_match_telegram('BTC', 'call', strike_lower, strike_higher,
                                                   lower_ask, higher_bid,
                                                   premium_match_config.btc_min_premium,
                                                   premium_match_config.eth_min_premium)
            
            higher_ask = strikes_data[strike_higher]['put']['ask']
            lower_bid = strikes_data[strike_lower]['put']['bid']
            if higher_ask > 0 and lower_bid > 0 and higher_ask == lower_bid:
                if higher_ask >= premium_match_config.btc_min_premium:
                    alert_key = f"BTC_PUT_{strike_higher}_{strike_lower}"
                    now = datetime.now().timestamp()
                    last_alert = last_premium_match_alert.get(alert_key, 0)
                    if now - last_alert >= premium_match_config.cooldown_seconds:
                        last_premium_match_alert[alert_key] = now
                        send_premium_match_telegram('BTC', 'put', strike_higher, strike_lower,
                                                   higher_ask, lower_bid,
                                                   premium_match_config.btc_min_premium,
                                                   premium_match_config.eth_min_premium)

# -------------------------------
# System 5: Premium Tracker Functions - IMMEDIATE ALERTS
# -------------------------------
def get_eth_symbol(eth_bot, strike: float, option_type: str) -> Optional[str]:
    if option_type == 'call':
        for s, symbol in eth_bot.option_chain_data['calls'].items():
            if s == strike:
                return symbol
    else:
        for s, symbol in eth_bot.option_chain_data['puts'].items():
            if s == strike:
                return symbol
    return None

def get_btc_symbol(btc_bot, strike: float, option_type: str) -> Optional[str]:
    if option_type == 'call':
        for s, symbol in btc_bot.option_chain_data['calls'].items():
            if s == strike:
                return symbol
    else:
        for s, symbol in btc_bot.option_chain_data['puts'].items():
            if s == strike:
                return symbol
    return None

def check_system5_eth(eth_bot):
    global premium_tracker_configs, system5_alert_counts
    
    config = premium_tracker_configs['eth_call']
    if config.active and config.strike > 0:
        symbol = get_eth_symbol(eth_bot, config.strike, 'call')
        if symbol and symbol in eth_bot.options_prices:
            current_ask = eth_bot.options_prices[symbol]['ask']
            if current_ask > 0:
                if config.last_ask_price > 0 and current_ask != config.last_ask_price:
                    send_system5_alert_telegram('ETH', 'call', config.strike, config.last_ask_price, current_ask)
                    system5_alert_counts['eth_call'] += 1
                config.last_ask_price = current_ask
    
    config = premium_tracker_configs['eth_put']
    if config.active and config.strike > 0:
        symbol = get_eth_symbol(eth_bot, config.strike, 'put')
        if symbol and symbol in eth_bot.options_prices:
            current_ask = eth_bot.options_prices[symbol]['ask']
            if current_ask > 0:
                if config.last_ask_price > 0 and current_ask != config.last_ask_price:
                    send_system5_alert_telegram('ETH', 'put', config.strike, config.last_ask_price, current_ask)
                    system5_alert_counts['eth_put'] += 1
                config.last_ask_price = current_ask

def check_system5_btc(btc_bot):
    global premium_tracker_configs, system5_alert_counts
    
    config = premium_tracker_configs['btc_call']
    if config.active and config.strike > 0:
        symbol = get_btc_symbol(btc_bot, config.strike, 'call')
        if symbol and symbol in btc_bot.options_prices:
            current_ask = btc_bot.options_prices[symbol]['ask']
            if current_ask > 0:
                if config.last_ask_price > 0 and current_ask != config.last_ask_price:
                    send_system5_alert_telegram('BTC', 'call', config.strike, config.last_ask_price, current_ask)
                    system5_alert_counts['btc_call'] += 1
                config.last_ask_price = current_ask
    
    config = premium_tracker_configs['btc_put']
    if config.active and config.strike > 0:
        symbol = get_btc_symbol(btc_bot, config.strike, 'put')
        if symbol and symbol in btc_bot.options_prices:
            current_ask = btc_bot.options_prices[symbol]['ask']
            if current_ask > 0:
                if config.last_ask_price > 0 and current_ask != config.last_ask_price:
                    send_system5_alert_telegram('BTC', 'put', config.strike, config.last_ask_price, current_ask)
                    system5_alert_counts['btc_put'] += 1
                config.last_ask_price = current_ask

# -------------------------------
# System 3: Dual Condition Detection Functions
# -------------------------------
def check_premium_spikes_eth(eth_bot):
    global price_history, last_spike_alert, last_spread_alert
    
    for symbol, price_data in eth_bot.options_prices.items():
        if not should_monitor_symbol(symbol):
            continue
        
        current_bid = price_data['bid']
        current_ask = price_data['ask']
        
        if current_bid <= 0 or current_ask <= 0:
            continue
        
        if spike_config.enabled_spike and spike_config.monitor_eth:
            if current_bid >= spike_config.spike_min_premium:
                if symbol not in price_history:
                    price_history[symbol] = []
                price_history[symbol].append(current_bid)
                if len(price_history[symbol]) > 10:
                    price_history[symbol] = price_history[symbol][-10:]
                if len(price_history[symbol]) >= 5:
                    historical_avg = sum(price_history[symbol][:-1]) / (len(price_history[symbol]) - 1)
                    if historical_avg > 0:
                        spike_percent = ((current_bid - historical_avg) / historical_avg) * 100
                        if spike_percent >= spike_config.min_spike_percent:
                            now = datetime.now().timestamp()
                            last_alert = last_spike_alert.get(symbol, 0)
                            if now - last_alert >= SPIKE_COOLDOWN_SECONDS:
                                send_spike_alert_telegram(symbol, current_bid, historical_avg, spike_percent)
                                last_spike_alert[symbol] = now
        
        if spike_config.enabled_spread and spike_config.monitor_eth:
            if current_bid >= spike_config.spread_min_premium:
                if current_bid > 0:
                    spread_percent = ((current_ask - current_bid) / current_bid) * 100
                    if spread_percent >= spike_config.min_spread_percent:
                        now = datetime.now().timestamp()
                        last_alert = last_spread_alert.get(symbol, 0)
                        if now - last_alert >= SPIKE_COOLDOWN_SECONDS:
                            send_spread_alert_telegram(symbol, current_bid, current_ask, spread_percent)
                            last_spread_alert[symbol] = now

def check_premium_spikes_btc(btc_bot):
    global price_history, last_spike_alert, last_spread_alert
    
    for symbol, price_data in btc_bot.options_prices.items():
        if not should_monitor_symbol(symbol):
            continue
        
        current_bid = price_data['bid']
        current_ask = price_data['ask']
        
        if current_bid <= 0 or current_ask <= 0:
            continue
        
        if spike_config.enabled_spike and spike_config.monitor_btc:
            if current_bid >= spike_config.spike_min_premium:
                if symbol not in price_history:
                    price_history[symbol] = []
                price_history[symbol].append(current_bid)
                if len(price_history[symbol]) > 10:
                    price_history[symbol] = price_history[symbol][-10:]
                if len(price_history[symbol]) >= 5:
                    historical_avg = sum(price_history[symbol][:-1]) / (len(price_history[symbol]) - 1)
                    if historical_avg > 0:
                        spike_percent = ((current_bid - historical_avg) / historical_avg) * 100
                        if spike_percent >= spike_config.min_spike_percent:
                            now = datetime.now().timestamp()
                            last_alert = last_spike_alert.get(symbol, 0)
                            if now - last_alert >= SPIKE_COOLDOWN_SECONDS:
                                send_spike_alert_telegram(symbol, current_bid, historical_avg, spike_percent)
                                last_spike_alert[symbol] = now
        
        if spike_config.enabled_spread and spike_config.monitor_btc:
            if current_bid >= spike_config.spread_min_premium:
                if current_bid > 0:
                    spread_percent = ((current_ask - current_bid) / current_bid) * 100
                    if spread_percent >= spike_config.min_spread_percent:
                        now = datetime.now().timestamp()
                        last_alert = last_spread_alert.get(symbol, 0)
                        if now - last_alert >= SPIKE_COOLDOWN_SECONDS:
                            send_spread_alert_telegram(symbol, current_bid, current_ask, spread_percent)
                            last_spread_alert[symbol] = now

def should_monitor_symbol(symbol: str) -> bool:
    if "BTC" in symbol and not spike_config.monitor_btc:
        return False
    if "ETH" in symbol and not spike_config.monitor_eth:
        return False
    parts = symbol.split('-')
    if len(parts) > 0:
        option_type = parts[0]
        if option_type == "C" and not spike_config.monitor_calls:
            return False
        if option_type == "P" and not spike_config.monitor_puts:
            return False
    return True

# -------------------------------
# ETH WebSocket Bot (simplified version)
# -------------------------------
class ETHWebSocketBot:
    def __init__(self):
        self.websocket_url = "wss://socket.india.delta.exchange"
        self.ws = None
        self.last_alert_time = {}
        self.options_prices = {}
        self.connected = False
        self.current_expiry = get_current_expiry()
        self.active_expiry = self.current_expiry
        self.active_symbols = []
        self.should_reconnect = True
        self.message_count = 0
        self.alert_count = 0
        self.option_chain_data = {'calls': {}, 'puts': {}}
        self.orderbook_data = {}

    def extract_expiry_from_symbol(self, symbol):
        try:
            parts = symbol.split('-')
            if len(parts) >= 4:
                return parts[3]
            return None
        except:
            return None

    def extract_strike(self, symbol):
        try:
            parts = symbol.split('-')
            for part in parts:
                if part.isdigit() and len(part) > 2:
                    return int(part)
            return 0
        except:
            return 0

    def on_open(self, ws):
        self.connected = True
        print(f"[{datetime.now()}] ✅ ETH: Connected to WebSocket")
        self.subscribe_to_options()

    def on_close(self, ws, close_status_code, close_msg):
        self.connected = False
        print(f"[{datetime.now()}] 🔴 ETH: WebSocket closed")
        if self.should_reconnect:
            sleep(10)
            self.connect()

    def on_error(self, ws, error):
        print(f"[{datetime.now()}] ❌ ETH: WebSocket error: {error}")

    def on_message(self, ws, message):
        try:
            message_json = json.loads(message)
            message_type = message_json.get('type')
            self.message_count += 1
            
            if message_type == 'l1_orderbook':
                self.process_l1_orderbook_data(message_json)
        except Exception as e:
            print(f"[{datetime.now()}] ❌ ETH: Message error: {e}")

    def process_l1_orderbook_data(self, message):
        try:
            symbol = message.get('symbol')
            best_bid = message.get('best_bid')
            best_ask = message.get('best_ask')
            
            if symbol and best_bid is not None and best_ask is not None:
                if 'ETH' not in symbol:
                    return
                
                self.options_prices[symbol] = {
                    'bid': float(best_bid) if best_bid else 0,
                    'ask': float(best_ask) if best_ask else 0,
                    'symbol': symbol
                }
                
                check_system5_eth(self)
                
        except Exception as e:
            print(f"[{datetime.now()}] ❌ ETH: Error processing: {e}")

    def subscribe_to_options(self):
        symbols = []
        try:
            url = "https://api.india.delta.exchange/v2/products"
            params = {'contract_types': 'call_options,put_options', 'states': 'live'}
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                products = response.json().get('result', [])
                for product in products:
                    symbol = product.get('symbol', '')
                    if 'ETH' in symbol:
                        symbols.append(symbol)
                        strike = self.extract_strike(symbol)
                        contract_type = product.get('contract_type', '')
                        if strike > 0:
                            if contract_type == 'call_options':
                                self.option_chain_data['calls'][strike] = symbol
                            else:
                                self.option_chain_data['puts'][strike] = symbol
        except Exception as e:
            print(f"[{datetime.now()}] ❌ ETH: Error fetching symbols: {e}")
        
        if symbols:
            payload = {"type": "subscribe", "payload": {"channels": [{"name": "l1_orderbook", "symbols": symbols}]}}
            self.ws.send(json.dumps(payload))
            print(f"[{datetime.now()}] 📡 ETH: Subscribed to {len(symbols)} symbols")

    def connect(self):
        print(f"[{datetime.now()}] 🌐 ETH: Connecting...")
        self.ws = websocket.WebSocketApp(self.websocket_url, on_open=self.on_open, on_message=self.on_message, on_error=self.on_error, on_close=self.on_close)
        self.ws.run_forever()

    def start(self):
        def run_bot():
            while self.should_reconnect:
                try:
                    self.connect()
                except Exception as e:
                    print(f"[{datetime.now()}] ❌ ETH: Connection error: {e}")
                    sleep(10)
        bot_thread = threading.Thread(target=run_bot)
        bot_thread.daemon = True
        bot_thread.start()

# -------------------------------
# BTC REST API Bot (simplified version)
# -------------------------------
class BTCRESTBot:
    def __init__(self):
        self.base_url = "https://api.india.delta.exchange/v2"
        self.last_alert_time = {}
        self.running = True
        self.fetch_count = 0
        self.alert_count = 0
        self.current_expiry = get_current_expiry()
        self.active_expiry = self.current_expiry
        self.active_symbols = []
        self.options_prices = {}
        self.option_chain_data = {'calls': {}, 'puts': {}}

    def extract_strike(self, symbol):
        try:
            parts = symbol.split('-')
            for part in parts:
                if part.isdigit() and len(part) > 2:
                    return int(part)
            return 0
        except:
            return 0

    def fetch_tickers(self):
        try:
            url = f"{self.base_url}/tickers"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return data.get('result', [])
        except Exception as e:
            print(f"[{datetime.now()}] ❌ BTC: Error: {e}")
        return []

    def process_btc_options(self):
        tickers = self.fetch_tickers()
        if not tickers:
            return {}
        
        self.option_chain_data = {'calls': {}, 'puts': {}}
        
        for ticker in tickers:
            symbol = ticker.get('symbol', '')
            if 'BTC' not in symbol:
                continue
            quotes = ticker.get('quotes', {})
            bid = float(quotes.get('best_bid', 0)) or 0
            ask = float(quotes.get('best_ask', 0)) or 0
            self.options_prices[symbol] = {'bid': bid, 'ask': ask, 'symbol': symbol}
            
            strike = self.extract_strike(symbol)
            if strike > 0:
                if symbol.startswith('C-'):
                    self.option_chain_data['calls'][strike] = symbol
                elif symbol.startswith('P-'):
                    self.option_chain_data['puts'][strike] = symbol
        
        return self.options_prices

    def start_monitoring(self):
        while self.running:
            try:
                self.fetch_count += 1
                self.process_btc_options()
                check_system5_btc(self)
                sleep(BTC_FETCH_INTERVAL)
            except Exception as e:
                print(f"[{datetime.now()}] ❌ BTC: Error: {e}")
                sleep(1)

    def stop(self):
        self.running = False

# -------------------------------
# Initialize Bots
# -------------------------------
eth_bot = ETHWebSocketBot()
btc_bot = BTCRESTBot()

# -------------------------------
# HTML Template - Complete Dark Mode
# -------------------------------
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quad Alert System - Dark Mode</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0e27; min-height: 100vh; padding: 20px; color: #e4e6eb; }
        .container { max-width: 1200px; margin: 0 auto; background: #1a1f3a; border-radius: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.5); overflow: hidden; border: 1px solid #2a2f4a; }
        .header { background: linear-gradient(135deg, #1e3a8a, #312e81); color: white; padding: 30px; text-align: center; }
        .header h1 { font-size: 2.5rem; margin-bottom: 10px; }
        .header .subtitle { font-size: 1.2rem; opacity: 0.9; }
        .tabs { display: flex; background: #0f142e; border-bottom: 2px solid #2a2f4a; flex-wrap: wrap; }
        .tab-btn { flex: 1; padding: 20px; border: none; background: none; font-size: 1.1rem; font-weight: 600; cursor: pointer; transition: all 0.3s ease; color: #9ca3af; }
        .tab-btn:hover { background: #1a1f3a; color: #60a5fa; }
        .tab-btn.active { background: #1a1f3a; color: #60a5fa; border-bottom: 3px solid #60a5fa; }
        .tab-content { display: none; padding: 30px; }
        .tab-content.active { display: block; }
        .alert-success { background: #064e3b; color: #34d399; padding: 15px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #059669; }
        .system-section { margin-bottom: 40px; }
        .section-title { font-size: 1.5rem; margin-bottom: 20px; color: #60a5fa; display: flex; align-items: center; gap: 10px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: #0f142e; padding: 25px; border-radius: 15px; border-left: 5px solid #60a5fa; }
        .stat-card h3 { color: #e4e6eb; margin-bottom: 15px; font-size: 1.3rem; }
        .stat-item { margin-bottom: 10px; font-size: 1.1rem; display: flex; justify-content: space-between; }
        .stat-label { color: #9ca3af; }
        .stat-value { font-weight: 600; color: #e4e6eb; }
        .threshold-card { background: #0f142e; padding: 25px; border-radius: 15px; margin-bottom: 20px; border: 1px solid #2a2f4a; }
        .threshold-card h3 { color: #e4e6eb; margin-bottom: 20px; font-size: 1.3rem; }
        .threshold-input { width: 100%; padding: 12px; font-size: 1.1rem; border: 2px solid #2a2f4a; border-radius: 10px; margin-bottom: 15px; background: #1a1f3a; color: #e4e6eb; }
        .update-btn { padding: 15px 30px; font-size: 1.1rem; font-weight: 600; border: none; border-radius: 10px; cursor: pointer; background: linear-gradient(135deg, #3b82f6, #6366f1); color: white; width: 100%; }
        .update-btn:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4); }
        .option-section { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .option-card { background: #0f142e; padding: 25px; border-radius: 15px; border-top: 5px solid; }
        .btc-call { border-color: #3b82f6; }
        .btc-put { border-color: #ef4444; }
        .eth-call { border-color: #10b981; }
        .eth-put { border-color: #8b5cf6; }
        .option-card h4 { font-size: 1.2rem; margin-bottom: 15px; color: #e4e6eb; }
        .select-input { width: 100%; padding: 12px; font-size: 1.1rem; border: 2px solid #2a2f4a; border-radius: 10px; margin-bottom: 15px; background: #1a1f3a; color: #e4e6eb; }
        .checkbox-group { display: flex; align-items: center; gap: 10px; margin-top: 15px; }
        .checkbox-group input[type="checkbox"] { width: 20px; height: 20px; cursor: pointer; }
        .activate-btn { padding: 20px; font-size: 1.3rem; font-weight: 700; border: none; border-radius: 15px; cursor: pointer; background: linear-gradient(135deg, #059669, #047857); color: white; width: 100%; margin-top: 20px; }
        .status-panel { background: #0f142e; padding: 25px; border-radius: 15px; margin-top: 30px; border: 1px solid #2a2f4a; }
        .status-panel h3 { color: #e4e6eb; margin-bottom: 20px; font-size: 1.3rem; }
        .status-item { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #2a2f4a; }
        .status-active { color: #10b981; }
        .status-inactive { color: #ef4444; }
        .dual-condition-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }
        @media (max-width: 768px) { .dual-condition-grid { grid-template-columns: 1fr; } }
        .condition-panel { padding: 25px; border-radius: 15px; margin-bottom: 20px; }
        .condition-1 { background: linear-gradient(135deg, #1e40af, #1e3a8a); color: white; }
        .condition-2 { background: linear-gradient(135deg, #6d28d9, #5b21b6); color: white; }
        .condition-panel h3 { color: white; margin-bottom: 20px; font-size: 1.5rem; }
        .condition-status { margin-bottom: 20px; padding: 15px; background: rgba(0,0,0,0.3); border-radius: 10px; }
        .start-btn { padding: 15px; font-size: 1.1rem; font-weight: 600; border: none; border-radius: 10px; cursor: pointer; background: #059669; color: white; flex: 1; }
        .stop-btn { padding: 15px; font-size: 1.1rem; font-weight: 600; border: none; border-radius: 10px; cursor: pointer; background: #dc2626; color: white; flex: 1; }
        .config-section { background: #0f142e; padding: 25px; border-radius: 15px; margin-bottom: 20px; border: 1px solid #2a2f4a; }
        .condition-section { background: #1a1f3a; padding: 20px; border-radius: 10px; margin-bottom: 20px; border-left: 4px solid; }
        .condition-1-section { border-left-color: #3b82f6; }
        .condition-2-section { border-left-color: #8b5cf6; }
        .checkbox-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-top: 20px; }
        .save-btn { padding: 15px 30px; font-size: 1.1rem; font-weight: 600; border: none; border-radius: 10px; cursor: pointer; background: #3b82f6; color: white; width: 100%; margin-top: 20px; }
        .system4-panel { background: linear-gradient(135deg, #d97706, #ea580c); color: white; }
        .cooldown-control { display: flex; gap: 10px; align-items: center; justify-content: center; margin-top: 15px; }
        .cooldown-btn { padding: 10px 20px; font-size: 1.2rem; font-weight: bold; border: none; border-radius: 8px; cursor: pointer; background: rgba(255,255,255,0.2); color: white; }
        .cooldown-input { width: 100px; text-align: center; padding: 10px; font-size: 1.1rem; border: 2px solid #f59e0b; border-radius: 8px; background: #1a1f3a; color: #e4e6eb; }
        .filter-input { width: 150px; text-align: center; padding: 10px; font-size: 1.1rem; border: 2px solid #f59e0b; border-radius: 8px; background: #1a1f3a; color: #e4e6eb; }
        .tracker-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .tracker-card { background: #0f142e; padding: 25px; border-radius: 15px; border-top: 5px solid; text-align: center; border: 1px solid #2a2f4a; }
        .tracker-card.monitoring { background: #064e3b; box-shadow: 0 0 20px rgba(5,150,105,0.3); }
        .footer { text-align: center; padding: 20px; color: #9ca3af; border-top: 1px solid #2a2f4a; margin-top: 30px; }
        .footer a { color: #60a5fa; text-decoration: none; }
        @media (max-width: 768px) { .tab-btn { padding: 15px; font-size: 0.9rem; } .tab-content { padding: 20px; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Quad Alert System</h1>
            <div class="subtitle">Arbitrage + Option Alerts + Spike Detection + Premium Match + Premium Tracker</div>
        </div>
        <div class="tabs">
            <button class="tab-btn active" onclick="showTab('arbitrage')">Arbitrage</button>
            <button class="tab-btn" onclick="showTab('option-alerts')">Option Alerts</button>
            <button class="tab-btn" onclick="showTab('spike-detector')">Spike Detector</button>
            <button class="tab-btn" onclick="showTab('premium-match')">Premium Match</button>
            <button class="tab-btn" onclick="showTab('premium-tracker')">Premium Tracker</button>
        </div>
        {% if success %}
        <div class="alert-success">✅ {{ success }}</div>
        {% endif %}
        <div id="arbitrage-tab" class="tab-content active">
            <div class="system-section">
                <h2 class="section-title">⚡ Arbitrage Alert System</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>🔵 ETH WebSocket Bot</h3>
                        <div class="stat-item"><span class="stat-label">Status:</span><span class="stat-value">{{ "✅ Connected" if eth_bot.connected else "🔴 Disconnected" }}</span></div>
                        <div class="stat-item"><span class="stat-label">Messages:</span><span class="stat-value">{{ eth_bot.message_count }}</span></div>
                        <div class="stat-item"><span class="stat-label">ETH Symbols:</span><span class="stat-value">{{ len(eth_bot.options_prices) }}</span></div>
                        <div class="stat-item"><span class="stat-label">ETH Alerts:</span><span class="stat-value">{{ eth_bot.alert_count }}</span></div>
                    </div>
                    <div class="stat-card">
                        <h3>🟠 BTC REST API Bot</h3>
                        <div class="stat-item"><span class="stat-label">Status:</span><span class="stat-value">{{ "✅ Running" if btc_bot.running else "🔴 Stopped" }}</span></div>
                        <div class="stat-item"><span class="stat-label">Fetches:</span><span class="stat-value">{{ btc_bot.fetch_count }}</span></div>
                        <div class="stat-item"><span class="stat-label">BTC Symbols:</span><span class="stat-value">{{ len(btc_bot.active_symbols) }}</span></div>
                        <div class="stat-item"><span class="stat-label">BTC Alerts:</span><span class="stat-value">{{ btc_bot.alert_count }}</span></div>
                    </div>
                </div>
                <div class="threshold-card">
                    <h3>⚙️ Update Arbitrage Thresholds</h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                        <div><h4>ETH Threshold: ${{ "%.2f"|format(DELTA_THRESHOLD['ETH']) }}</h4>
                        <form action="/update_eth_threshold" method="POST"><input type="number" name="threshold" value="{{ "%.2f"|format(DELTA_THRESHOLD['ETH']) }}" step="0.01" min="0.01" max="10" class="threshold-input" required><button type="submit" class="update-btn">Update ETH Threshold</button></form></div>
                        <div><h4>BTC Threshold: ${{ "%.2f"|format(DELTA_THRESHOLD['BTC']) }}</h4>
                        <form action="/update_btc_threshold" method="POST"><input type="number" name="threshold" value="{{ "%.2f"|format(DELTA_THRESHOLD['BTC']) }}" step="0.01" min="0.01" max="50" class="threshold-input" required><button type="submit" class="update-btn">Update BTC Threshold</button></form></div>
                    </div>
                </div>
            </div>
        </div>
        <div id="option-alerts-tab" class="tab-content">
            <div class="system-section">
                <h2 class="section-title">🎯 Option Strike Alert System</h2>
                <p style="margin-bottom: 20px; color: #9ca3af;">Configure alerts for specific strikes and premiums</p>
                <form action="/activate_alerts" method="POST">
                    <div class="option-section">
                        <div class="option-card btc-call"><h4>🔵 BTC CALL OPTIONS</h4>
                        <select name="btc_call_strike" class="select-input"><option value="">Select Strike</option>{% for strike in btc_bot.option_chain_data.calls.keys()|sort %}<option value="{{ strike }}" {% if alert_configs['btc_call'].strike == strike %}selected{% endif %}>{{ strike }}</option>{% endfor %}</select>
                        <input type="number" name="btc_call_premium" placeholder="Premium ($)" value="{{ "%.2f"|format(alert_configs['btc_call'].premium) if alert_configs['btc_call'].premium > 0 else '' }}" step="0.01" min="0" class="threshold-input">
                        <div class="checkbox-group"><input type="checkbox" name="btc_call_monitor" id="btc_call_monitor" {% if alert_configs['btc_call'].is_monitoring %}checked{% endif %}><label for="btc_call_monitor">Monitor BTC Calls</label></div></div>
                        <div class="option-card btc-put"><h4>🔴 BTC PUT OPTIONS</h4>
                        <select name="btc_put_strike" class="select-input"><option value="">Select Strike</option>{% for strike in btc_bot.option_chain_data.puts.keys()|sort %}<option value="{{ strike }}" {% if alert_configs['btc_put'].strike == strike %}selected{% endif %}>{{ strike }}</option>{% endfor %}</select>
                        <input type="number" name="btc_put_premium" placeholder="Premium ($)" value="{{ "%.2f"|format(alert_configs['btc_put'].premium) if alert_configs['btc_put'].premium > 0 else '' }}" step="0.01" min="0" class="threshold-input">
                        <div class="checkbox-group"><input type="checkbox" name="btc_put_monitor" id="btc_put_monitor" {% if alert_configs['btc_put'].is_monitoring %}checked{% endif %}><label for="btc_put_monitor">Monitor BTC Puts</label></div></div>
                        <div class="option-card eth-call"><h4>🟢 ETH CALL OPTIONS</h4>
                        <select name="eth_call_strike" class="select-input"><option value="">Select Strike</option>{% for strike in eth_bot.option_chain_data.calls.keys()|sort %}<option value="{{ strike }}" {% if alert_configs['eth_call'].strike == strike %}selected{% endif %}>{{ strike }}</option>{% endfor %}</select>
                        <input type="number" name="eth_call_premium" placeholder="Premium ($)" value="{{ "%.2f"|format(alert_configs['eth_call'].premium) if alert_configs['eth_call'].premium > 0 else '' }}" step="0.01" min="0" class="threshold-input">
                        <div class="checkbox-group"><input type="checkbox" name="eth_call_monitor" id="eth_call_monitor" {% if alert_configs['eth_call'].is_monitoring %}checked{% endif %}><label for="eth_call_monitor">Monitor ETH Calls</label></div></div>
                        <div class="option-card eth-put"><h4>🟣 ETH PUT OPTIONS</h4>
                        <select name="eth_put_strike" class="select-input"><option value="">Select Strike</option>{% for strike in eth_bot.option_chain_data.puts.keys()|sort %}<option value="{{ strike }}" {% if alert_configs['eth_put'].strike == strike %}selected{% endif %}>{{ strike }}</option>{% endfor %}</select>
                        <input type="number" name="eth_put_premium" placeholder="Premium ($)" value="{{ "%.2f"|format(alert_configs['eth_put'].premium) if alert_configs['eth_put'].premium > 0 else '' }}" step="0.01" min="0" class="threshold-input">
                        <div class="checkbox-group"><input type="checkbox" name="eth_put_monitor" id="eth_put_monitor" {% if alert_configs['eth_put'].is_monitoring %}checked{% endif %}><label for="eth_put_monitor">Monitor ETH Puts</label></div></div>
                    </div>
                    <button type="submit" class="activate-btn">🚀 ACTIVATE ALERTS</button>
                </form>
                <div class="status-panel"><h3>📊 Active Alerts Status</h3>
                    <div class="status-item"><span class="status-label">BTC Calls:</span><span class="status-value {% if alert_configs['btc_call'].is_monitoring %}status-active{% else %}status-inactive{% endif %}">{% if alert_configs['btc_call'].is_monitoring %}✅ ACTIVE{% else %}❌ INACTIVE{% endif %}</span></div>
                    <div class="status-item"><span class="status-label">BTC Puts:</span><span class="status-value {% if alert_configs['btc_put'].is_monitoring %}status-active{% else %}status-inactive{% endif %}">{% if alert_configs['btc_put'].is_monitoring %}✅ ACTIVE{% else %}❌ INACTIVE{% endif %}</span></div>
                    <div class="status-item"><span class="status-label">ETH Calls:</span><span class="status-value {% if alert_configs['eth_call'].is_monitoring %}status-active{% else %}status-inactive{% endif %}">{% if alert_configs['eth_call'].is_monitoring %}✅ ACTIVE{% else %}❌ INACTIVE{% endif %}</span></div>
                    <div class="status-item"><span class="status-label">ETH Puts:</span><span class="status-value {% if alert_configs['eth_put'].is_monitoring %}status-active{% else %}status-inactive{% endif %}">{% if alert_configs['eth_put'].is_monitoring %}✅ ACTIVE{% else %}❌ INACTIVE{% endif %}</span></div>
                </div>
            </div>
        </div>
        <div id="spike-detector-tab" class="tab-content">
            <div class="system-section">
                <h2 class="section-title">🚨 DUAL CONDITION SPIKE DETECTOR</h2>
                <div class="dual-condition-grid">
                    <div class="condition-panel condition-1"><h3>📊 CONDITION 1: PRICE SPIKE</h3>
                        <div class="condition-status"><strong>Status:</strong> <span style="color: {% if spike_config.enabled_spike %}#10b981{% else %}#ef4444{% endif %};">{% if spike_config.enabled_spike %}🟢 RUNNING{% else %}🔴 STOPPED{% endif %}</span></div>
                        <div class="condition-controls"><form action="/start_spike_detection" method="POST"><button type="submit" class="start-btn">▶️ START SPIKE</button></form><form action="/stop_spike_detection" method="POST"><button type="submit" class="stop-btn">⏸️ STOP SPIKE</button></form></div>
                    </div>
                    <div class="condition-panel condition-2"><h3>📊 CONDITION 2: BID-ASK SPREAD</h3>
                        <div class="condition-status"><strong>Status:</strong> <span style="color: {% if spike_config.enabled_spread %}#10b981{% else %}#ef4444{% endif %};">{% if spike_config.enabled_spread %}🟢 RUNNING{% else %}🔴 STOPPED{% endif %}</span></div>
                        <div class="condition-controls"><form action="/start_spread_detection" method="POST"><button type="submit" class="start-btn">▶️ START SPREAD</button></form><form action="/stop_spread_detection" method="POST"><button type="submit" class="stop-btn">⏸️ STOP SPREAD</button></form></div>
                    </div>
                </div>
                <div class="config-section"><h4>Configuration Settings</h4>
                <form action="/update_spike_config" method="POST">
                    <div class="condition-section condition-1-section"><h5>📊 CONDITION 1: PRICE SPIKE</h5>
                        <div class="config-row"><label>Minimum Spike Percentage:</label><input type="number" name="min_spike_percent" value="{{ spike_config.min_spike_percent }}" step="0.1" class="threshold-input" required></div>
                        <div class="config-row"><label>Minimum Premium Filter:</label><input type="number" name="spike_min_premium" value="{{ spike_config.spike_min_premium }}" step="0.01" min="0" class="threshold-input" required></div>
                    </div>
                    <div class="condition-section condition-2-section"><h5>📊 CONDITION 2: BID-ASK SPREAD</h5>
                        <div class="config-row"><label>Minimum Spread Percentage:</label><input type="number" name="min_spread_percent" value="{{ spike_config.min_spread_percent }}" step="0.1" class="threshold-input" required></div>
                        <div class="config-row"><label>Minimum Premium Filter:</label><input type="number" name="spread_min_premium" value="{{ spike_config.spread_min_premium }}" step="0.01" min="0" class="threshold-input" required></div>
                    </div>
                    <div class="checkbox-grid"><div class="checkbox-group"><input type="checkbox" id="monitor_eth" name="monitor_eth" {% if spike_config.monitor_eth %}checked{% endif %}><label for="monitor_eth">Monitor ETH</label></div>
                    <div class="checkbox-group"><input type="checkbox" id="monitor_btc" name="monitor_btc" {% if spike_config.monitor_btc %}checked{% endif %}><label for="monitor_btc">Monitor BTC</label></div>
                    <div class="checkbox-group"><input type="checkbox" id="monitor_calls" name="monitor_calls" {% if spike_config.monitor_calls %}checked{% endif %}><label for="monitor_calls">Include Calls</label></div>
                    <div class="checkbox-group"><input type="checkbox" id="monitor_puts" name="monitor_puts" {% if spike_config.monitor_puts %}checked{% endif %}><label for="monitor_puts">Include Puts</label></div></div>
                    <button type="submit" class="save-btn">💾 SAVE SETTINGS</button>
                </form></div>
            </div>
        </div>
        <div id="premium-match-tab" class="tab-content">
            <div class="system-section">
                <h2 class="section-title">🎯 EXACT PREMIUM MATCH DETECTOR</h2>
                <div class="condition-panel system4-panel"><h3>📊 SYSTEM 4 STATUS</h3>
                    <div class="condition-status"><strong>Status:</strong> <span style="color: {% if system4_active %}#10b981{% else %}#ef4444{% endif %};">{% if system4_active %}🟢 RUNNING{% else %}🔴 STOPPED{% endif %}</span></div>
                    <div class="condition-controls" style="display: flex; gap: 15px;"><form action="/start_system4" method="POST" style="flex:1"><button type="submit" class="start-btn">▶️ START SYSTEM 4</button></form><form action="/stop_system4" method="POST" style="flex:1"><button type="submit" class="stop-btn">⏸️ STOP SYSTEM 4</button></form></div>
                </div>
                <div class="config-section"><h4>⚙️ COOLDOWN CONFIGURATION</h4>
                <form action="/update_system4_cooldown" method="POST"><div class="config-row"><label>Cooldown Duration (seconds):</label><div class="cooldown-control"><button type="button" onclick="decrementCooldown()" class="cooldown-btn">-</button><input type="number" id="cooldown_seconds" name="cooldown_seconds" value="{{ premium_match_config.cooldown_seconds }}" step="5" min="5" max="300" class="cooldown-input"><button type="button" onclick="incrementCooldown()" class="cooldown-btn">+</button></div></div><button type="submit" class="save-btn">💾 UPDATE COOLDOWN</button></form></div>
                <div class="config-section"><h4>💰 BTC PREMIUM FILTER</h4>
                <form action="/update_system4_btc_filter" method="POST"><div class="config-row"><label>BTC Minimum Premium ($):</label><div class="cooldown-control"><button type="button" onclick="decrementBtcFilter()" class="cooldown-btn">-</button><input type="number" id="btc_min_premium" name="btc_min_premium" value="{{ premium_match_config.btc_min_premium }}" step="0.5" min="0" max="1000" class="filter-input"><button type="button" onclick="incrementBtcFilter()" class="cooldown-btn">+</button></div></div><button type="submit" class="save-btn">💾 UPDATE BTC FILTER</button></form></div>
                <div class="config-section"><h4>💰 ETH PREMIUM FILTER</h4>
                <form action="/update_system4_eth_filter" method="POST"><div class="config-row"><label>ETH Minimum Premium ($):</label><div class="cooldown-control"><button type="button" onclick="decrementEthFilter()" class="cooldown-btn">-</button><input type="number" id="eth_min_premium" name="eth_min_premium" value="{{ premium_match_config.eth_min_premium }}" step="0.01" min="0.01" max="500" class="filter-input"><button type="button" onclick="incrementEthFilter()" class="cooldown-btn">+</button></div></div><button type="submit" class="save-btn">💾 UPDATE ETH FILTER</button></form></div>
            </div>
        </div>
        <div id="premium-tracker-tab" class="tab-content">
            <div class="system-section">
                <h2 class="section-title">⚡ PREMIUM TRACKER (NO DELAY - IMMEDIATE ALERTS)</h2>
                <p style="margin-bottom: 20px; color: #10b981;">⚠️ Alerts are sent IMMEDIATELY when price changes - No cooldown delay!</p>
                <div class="tracker-grid">
                    <div class="tracker-card btc-call {% if premium_tracker_configs['btc_call'].active %}monitoring{% endif %}"><h4>🔵 BTC CALL</h4>
                    <form action="/start_system5_btc_call" method="POST"><select name="strike" class="select-input" {% if premium_tracker_configs['btc_call'].active %}disabled{% endif %}><option value="">Select Strike</option>{% for strike in btc_bot.option_chain_data.calls.keys()|sort %}<option value="{{ strike }}" {% if premium_tracker_configs['btc_call'].strike == strike %}selected{% endif %}>{{ strike }}</option>{% endfor %}</select>
                    {% if premium_tracker_configs['btc_call'].active %}<p>Last Ask: ${{ "%.2f"|format(premium_tracker_configs['btc_call'].last_ask_price) }}</p><p class="status-active">🟢 MONITORING (IMMEDIATE)</p><button type="button" class="stop-btn" onclick="location.href='/stop_system5_btc_call'" style="width:100%">⏸️ STOP</button>{% else %}<p>Last Ask: --</p><p class="status-inactive">🔴 INACTIVE</p><button type="submit" class="start-btn" style="width:100%">▶️ START</button>{% endif %}</form></div>
                    <div class="tracker-card btc-put {% if premium_tracker_configs['btc_put'].active %}monitoring{% endif %}"><h4>🔴 BTC PUT</h4>
                    <form action="/start_system5_btc_put" method="POST"><select name="strike" class="select-input" {% if premium_tracker_configs['btc_put'].active %}disabled{% endif %}><option value="">Select Strike</option>{% for strike in btc_bot.option_chain_data.puts.keys()|sort %}<option value="{{ strike }}" {% if premium_tracker_configs['btc_put'].strike == strike %}selected{% endif %}>{{ strike }}</option>{% endfor %}</select>
                    {% if premium_tracker_configs['btc_put'].active %}<p>Last Ask: ${{ "%.2f"|format(premium_tracker_configs['btc_put'].last_ask_price) }}</p><p class="status-active">🟢 MONITORING (IMMEDIATE)</p><button type="button" class="stop-btn" onclick="location.href='/stop_system5_btc_put'" style="width:100%">⏸️ STOP</button>{% else %}<p>Last Ask: --</p><p class="status-inactive">🔴 INACTIVE</p><button type="submit" class="start-btn" style="width:100%">▶️ START</button>{% endif %}</form></div>
                    <div class="tracker-card eth-call {% if premium_tracker_configs['eth_call'].active %}monitoring{% endif %}"><h4>🟢 ETH CALL</h4>
                    <form action="/start_system5_eth_call" method="POST"><select name="strike" class="select-input" {% if premium_tracker_configs['eth_call'].active %}disabled{% endif %}><option value="">Select Strike</option>{% for strike in eth_bot.option_chain_data.calls.keys()|sort %}<option value="{{ strike }}" {% if premium_tracker_configs['eth_call'].strike == strike %}selected{% endif %}>{{ strike }}</option>{% endfor %}</select>
                    {% if premium_tracker_configs['eth_call'].active %}<p>Last Ask: ${{ "%.2f"|format(premium_tracker_configs['eth_call'].last_ask_price) }}</p><p class="status-active">🟢 MONITORING (IMMEDIATE)</p><button type="button" class="stop-btn" onclick="location.href='/stop_system5_eth_call'" style="width:100%">⏸️ STOP</button>{% else %}<p>Last Ask: --</p><p class="status-inactive">🔴 INACTIVE</p><button type="submit" class="start-btn" style="width:100%">▶️ START</button>{% endif %}</form></div>
                    <div class="tracker-card eth-put {% if premium_tracker_configs['eth_put'].active %}monitoring{% endif %}"><h4>🟣 ETH PUT</h4>
                    <form action="/start_system5_eth_put" method="POST"><select name="strike" class="select-input" {% if premium_tracker_configs['eth_put'].active %}disabled{% endif %}><option value="">Select Strike</option>{% for strike in eth_bot.option_chain_data.puts.keys()|sort %}<option value="{{ strike }}" {% if premium_tracker_configs['eth_put'].strike == strike %}selected{% endif %}>{{ strike }}</option>{% endfor %}</select>
                    {% if premium_tracker_configs['eth_put'].active %}<p>Last Ask: ${{ "%.2f"|format(premium_tracker_configs['eth_put'].last_ask_price) }}</p><p class="status-active">🟢 MONITORING (IMMEDIATE)</p><button type="button" class="stop-btn" onclick="location.href='/stop_system5_eth_put'" style="width:100%">⏸️ STOP</button>{% else %}<p>Last Ask: --</p><p class="status-inactive">🔴 INACTIVE</p><button type="submit" class="start-btn" style="width:100%">▶️ START</button>{% endif %}</form></div>
                </div>
            </div>
        </div>
        <div class="footer"><p>Auto-expiry at 5:30 PM IST • All systems running simultaneously</p><p>⚡ System 5: Immediate alerts - No delay on price changes!</p><p>Last Update: {{ get_ist_time() }} • <a href="/health">Health Check</a></p></div>
    </div>
    <script>
        function showTab(tabName) { document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active')); document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active')); document.getElementById(tabName + '-tab').classList.add('active'); event.target.classList.add('active'); }
        function decrementCooldown() { let input = document.getElementById('cooldown_seconds'); let v = parseInt(input.value); if (v > 5) input.value = v - 5; }
        function incrementCooldown() { let input = document.getElementById('cooldown_seconds'); let v = parseInt(input.value); if (v < 300) input.value = v + 5; }
        function decrementBtcFilter() { let input = document.getElementById('btc_min_premium'); let v = parseFloat(input.value); if (v >= 0.5) input.value = (v - 0.5).toFixed(1); else if (v > 0) input.value = 0; }
        function incrementBtcFilter() { let input = document.getElementById('btc_min_premium'); let v = parseFloat(input.value); if (v <= 999.5) input.value = (v + 0.5).toFixed(1); }
        function decrementEthFilter() { let input = document.getElementById('eth_min_premium'); let v = parseFloat(input.value); if (v >= 0.01) input.value = (v - 0.01).toFixed(2); }
        function incrementEthFilter() { let input = document.getElementById('eth_min_premium'); let v = parseFloat(input.value); if (v <= 499.99) input.value = (v + 0.01).toFixed(2); }
        setTimeout(function() { window.location.reload(); }, 30000);
    </script>
</body>
</html>
'''

# -------------------------------
# Flask Routes
# -------------------------------
@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, 
                                 eth_bot=eth_bot,
                                 btc_bot=btc_bot,
                                 alert_configs=alert_configs,
                                 spike_config=spike_config,
                                 premium_match_config=premium_match_config,
                                 premium_tracker_configs=premium_tracker_configs,
                                 DELTA_THRESHOLD=DELTA_THRESHOLD,
                                 new_system_active=new_system_active,
                                 system4_active=system4_active,
                                 get_ist_time=get_ist_time,
                                 format_expiry_display=format_expiry_display,
                                 success=request.args.get('success'),
                                 len=len)

@app.route('/activate_alerts', methods=['POST'])
def activate_alerts():
    global new_system_active, alert_configs
    
    try:
        old_configs = {}
        for config_id, config in alert_configs.items():
            old_configs[config_id] = asdict(config)
        
        btc_call_strike_str = request.form.get('btc_call_strike', '')
        btc_call_strike = float(btc_call_strike_str) if btc_call_strike_str else 0
        btc_call_premium_str = request.form.get('btc_call_premium', '')
        btc_call_premium = float(btc_call_premium_str) if btc_call_premium_str else 0
        btc_call_monitor = 'btc_call_monitor' in request.form
        
        alert_configs['btc_call'].strike = btc_call_strike
        alert_configs['btc_call'].premium = btc_call_premium
        alert_configs['btc_call'].is_monitoring = btc_call_monitor
        alert_configs['btc_call'].last_updated = datetime.now().isoformat()
        alert_configs['btc_call'].active_expiry = btc_bot.active_expiry
        
        btc_put_strike_str = request.form.get('btc_put_strike', '')
        btc_put_strike = float(btc_put_strike_str) if btc_put_strike_str else 0
        btc_put_premium_str = request.form.get('btc_put_premium', '')
        btc_put_premium = float(btc_put_premium_str) if btc_put_premium_str else 0
        btc_put_monitor = 'btc_put_monitor' in request.form
        
        alert_configs['btc_put'].strike = btc_put_strike
        alert_configs['btc_put'].premium = btc_put_premium
        alert_configs['btc_put'].is_monitoring = btc_put_monitor
        alert_configs['btc_put'].last_updated = datetime.now().isoformat()
        alert_configs['btc_put'].active_expiry = btc_bot.active_expiry
        
        eth_call_strike_str = request.form.get('eth_call_strike', '')
        eth_call_strike = float(eth_call_strike_str) if eth_call_strike_str else 0
        eth_call_premium_str = request.form.get('eth_call_premium', '')
        eth_call_premium = float(eth_call_premium_str) if eth_call_premium_str else 0
        eth_call_monitor = 'eth_call_monitor' in request.form
        
        alert_configs['eth_call'].strike = eth_call_strike
        alert_configs['eth_call'].premium = eth_call_premium
        alert_configs['eth_call'].is_monitoring = eth_call_monitor
        alert_configs['eth_call'].last_updated = datetime.now().isoformat()
        alert_configs['eth_call'].active_expiry = eth_bot.active_expiry
        
        eth_put_strike_str = request.form.get('eth_put_strike', '')
        eth_put_strike = float(eth_put_strike_str) if eth_put_strike_str else 0
        eth_put_premium_str = request.form.get('eth_put_premium', '')
        eth_put_premium = float(eth_put_premium_str) if eth_put_premium_str else 0
        eth_put_monitor = 'eth_put_monitor' in request.form
        
        alert_configs['eth_put'].strike = eth_put_strike
        alert_configs['eth_put'].premium = eth_put_premium
        alert_configs['eth_put'].is_monitoring = eth_put_monitor
        alert_configs['eth_put'].last_updated = datetime.now().isoformat()
        alert_configs['eth_put'].active_expiry = eth_bot.active_expiry
        
        new_system_active = any(config.is_monitoring for config in alert_configs.values())
        
        for config_id in alert_configs:
            new_config = asdict(alert_configs[config_id])
            old_config = old_configs.get(config_id, {})
            
            if (old_config.get('strike', 0) != new_config['strike'] or
                old_config.get('premium', 0) != new_config['premium'] or
                old_config.get('is_monitoring', False) != new_config['is_monitoring']):
                
                send_config_update_telegram(config_id, old_config, new_config)
        
        if new_system_active:
            active_count = sum(1 for config in alert_configs.values() if config.is_monitoring)
            send_telegram(f"🚀 OPTION ALERT SYSTEM ACTIVATED!\n\n📊 Active alerts: {active_count}/4\n⏰ Time: {get_ist_time()}\n\nSystem is now monitoring configured alerts!")
        else:
            send_telegram(f"⏸️ OPTION ALERT SYSTEM DEACTIVATED\n\n⏰ Time: {get_ist_time()}\n\nNo alerts are currently monitored.")
        
        return redirect('/?success=Alert+system+activated+successfully!')
        
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error activating alerts: {e}")
        return redirect('/?success=Error+activating+alerts')

@app.route('/update_eth_threshold', methods=['POST'])
def update_eth_threshold():
    try:
        new_threshold = float(request.form['threshold'])
        if new_threshold <= 0:
            return "Threshold must be positive", 400
        DELTA_THRESHOLD['ETH'] = new_threshold
        send_telegram(f"⚙️ ETH Arbitrage Threshold Updated\n\n📊 New Value: ${new_threshold:.2f}\n⏰ Time: {get_ist_time()}")
        return redirect('/?success=ETH+threshold+updated+successfully!')
    except ValueError:
        return "Invalid threshold value", 400

@app.route('/update_btc_threshold', methods=['POST'])
def update_btc_threshold():
    try:
        new_threshold = float(request.form['threshold'])
        if new_threshold <= 0:
            return "Threshold must be positive", 400
        DELTA_THRESHOLD['BTC'] = new_threshold
        send_telegram(f"⚙️ BTC Arbitrage Threshold Updated\n\n📊 New Value: ${new_threshold:.2f}\n⏰ Time: {get_ist_time()}")
        return redirect('/?success=BTC+threshold+updated+successfully!')
    except ValueError:
        return "Invalid threshold value", 400

@app.route('/start_spike_detection', methods=['POST'])
def start_spike_detection():
    global spike_config
    if not spike_config.enabled_spike:
        spike_config.enabled_spike = True
        send_telegram(f"🚨 PRICE SPIKE DETECTION STARTED!\n\n⚡ Minimum Spike: {spike_config.min_spike_percent}%\n💰 Minimum Premium: ${spike_config.spike_min_premium:.2f}\n⏰ Time: {get_ist_time()}")
    return redirect('/?success=Spike+detection+started!')

@app.route('/stop_spike_detection', methods=['POST'])
def stop_spike_detection():
    global spike_config
    if spike_config.enabled_spike:
        spike_config.enabled_spike = False
        send_telegram(f"⏸️ PRICE SPIKE DETECTION STOPPED\n\n⏰ Time: {get_ist_time()}")
    return redirect('/?success=Spike+detection+stopped!')

@app.route('/start_spread_detection', methods=['POST'])
def start_spread_detection():
    global spike_config
    if not spike_config.enabled_spread:
        spike_config.enabled_spread = True
        send_telegram(f"🚨 BID-ASK SPREAD DETECTION STARTED!\n\n⚡ Minimum Spread: {spike_config.min_spread_percent}%\n💰 Minimum Premium: ${spike_config.spread_min_premium:.2f}\n⏰ Time: {get_ist_time()}")
    return redirect('/?success=Spread+detection+started!')

@app.route('/stop_spread_detection', methods=['POST'])
def stop_spread_detection():
    global spike_config
    if spike_config.enabled_spread:
        spike_config.enabled_spread = False
        send_telegram(f"⏸️ BID-ASK SPREAD DETECTION STOPPED\n\n⏰ Time: {get_ist_time()}")
    return redirect('/?success=Spread+detection+stopped!')

@app.route('/update_spike_config', methods=['POST'])
def update_spike_config():
    global spike_config
    try:
        spike_config.min_spike_percent = float(request.form.get('min_spike_percent', 100.0))
        spike_config.spike_min_premium = float(request.form.get('spike_min_premium', 1.0))
        spike_config.min_spread_percent = float(request.form.get('min_spread_percent', 100.0))
        spike_config.spread_min_premium = float(request.form.get('spread_min_premium', 0.5))
        spike_config.monitor_eth = 'monitor_eth' in request.form
        spike_config.monitor_btc = 'monitor_btc' in request.form
        spike_config.monitor_calls = 'monitor_calls' in request.form
        spike_config.monitor_puts = 'monitor_puts' in request.form
        send_telegram(f"⚙️ DUAL CONDITION CONFIG UPDATED\n\n📊 Spike: {spike_config.min_spike_percent}%\n💰 Min Premium: ${spike_config.spike_min_premium:.2f}\n📊 Spread: {spike_config.min_spread_percent}%\n💰 Min Premium: ${spike_config.spread_min_premium:.2f}\n⏰ Time: {get_ist_time()}")
        return redirect('/?success=Spike+detector+configuration+updated!')
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error: {e}")
        return redirect('/?success=Error+updating+configuration')

@app.route('/start_system4', methods=['POST'])
def start_system4():
    global system4_active, system4_start_time, premium_match_config
    if not system4_active:
        system4_active = True
        premium_match_config.enabled = True
        system4_start_time = get_ist_time()
        send_telegram(f"🎯 SYSTEM 4: EXACT PREMIUM MATCH DETECTION STARTED!\n\n⚡ Cooldown: {premium_match_config.cooldown_seconds}s\n💰 BTC Filter: ≥ ${premium_match_config.btc_min_premium:.2f}\n💰 ETH Filter: ≥ ${premium_match_config.eth_min_premium:.2f}\n⏰ Time: {get_ist_time()}")
    return redirect('/?success=System+4+started!')

@app.route('/stop_system4', methods=['POST'])
def stop_system4():
    global system4_active, premium_match_config
    if system4_active:
        system4_active = False
        premium_match_config.enabled = False
        send_telegram(f"⏸️ SYSTEM 4: EXACT PREMIUM MATCH DETECTION STOPPED\n\n⏰ Time: {get_ist_time()}")
    return redirect('/?success=System+4+stopped!')

@app.route('/update_system4_cooldown', methods=['POST'])
def update_system4_cooldown():
    global premium_match_config
    try:
        old_cooldown = premium_match_config.cooldown_seconds
        new_cooldown = int(request.form.get('cooldown_seconds', 60))
        if new_cooldown < 5:
            new_cooldown = 5
        if new_cooldown > 300:
            new_cooldown = 300
        premium_match_config.cooldown_seconds = new_cooldown
        send_telegram(f"⚙️ SYSTEM 4 COOLDOWN UPDATED\n\n⏰ {old_cooldown}s → {new_cooldown}s\n⏰ Time: {get_ist_time()}")
        return redirect('/?success=System+4+cooldown+updated+successfully!')
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error: {e}")
        return redirect('/?success=Error+updating+cooldown')

@app.route('/update_system4_btc_filter', methods=['POST'])
def update_system4_btc_filter():
    global premium_match_config
    try:
        old_filter = premium_match_config.btc_min_premium
        new_filter = float(request.form.get('btc_min_premium', 0))
        if new_filter < 0:
            new_filter = 0
        if new_filter > 1000:
            new_filter = 1000
        premium_match_config.btc_min_premium = new_filter
        send_telegram(f"💰 SYSTEM 4 BTC FILTER UPDATED\n\n📊 ≥ ${old_filter:.2f} → ≥ ${new_filter:.2f}\n⏰ Time: {get_ist_time()}")
        return redirect('/?success=BTC+filter+updated+successfully!')
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error: {e}")
        return redirect('/?success=Error+updating+BTC+filter')

@app.route('/update_system4_eth_filter', methods=['POST'])
def update_system4_eth_filter():
    global premium_match_config
    try:
        old_filter = premium_match_config.eth_min_premium
        new_filter = float(request.form.get('eth_min_premium', 0))
        if new_filter < 0.01:
            new_filter = 0.01
        if new_filter > 500:
            new_filter = 500
        premium_match_config.eth_min_premium = new_filter
        send_telegram(f"💰 SYSTEM 4 ETH FILTER UPDATED\n\n📊 ≥ ${old_filter:.2f} → ≥ ${new_filter:.2f}\n⏰ Time: {get_ist_time()}")
        return redirect('/?success=ETH+filter+updated+successfully!')
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error: {e}")
        return redirect('/?success=Error+updating+ETH+filter')

@app.route('/start_system5_btc_call', methods=['POST'])
def start_system5_btc_call():
    global premium_tracker_configs
    try:
        strike_str = request.form.get('strike', '')
        if not strike_str:
            return redirect('/?success=Please+select+a+strike')
        strike = float(strike_str)
        config = premium_tracker_configs['btc_call']
        config.active = True
        config.strike = strike
        symbol = get_btc_symbol(btc_bot, strike, 'call')
        if symbol and symbol in btc_bot.options_prices:
            config.last_ask_price = btc_bot.options_prices[symbol]['ask']
        send_telegram(f"🔔 SYSTEM 5: BTC {strike} CALL TRACKING STARTED (IMMEDIATE ALERTS - NO DELAY)\n\n💰 Initial Ask: ${config.last_ask_price:.2f}\n⚡ Every price change will trigger an immediate alert!\n⏰ Time: {get_ist_time()}")
        return redirect('/?success=BTC+CALL+tracking+started!+(Immediate+alerts)')
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error: {e}")
        return redirect('/?success=Error+starting+tracker')

@app.route('/stop_system5_btc_call')
def stop_system5_btc_call():
    global premium_tracker_configs
    config = premium_tracker_configs['btc_call']
    config.active = False
    config.last_ask_price = 0.0
    send_telegram(f"⏸️ SYSTEM 5: BTC CALL TRACKING STOPPED\n\n⏰ Time: {get_ist_time()}")
    return redirect('/?success=BTC+CALL+tracking+stopped!')

@app.route('/start_system5_btc_put', methods=['POST'])
def start_system5_btc_put():
    global premium_tracker_configs
    try:
        strike_str = request.form.get('strike', '')
        if not strike_str:
            return redirect('/?success=Please+select+a+strike')
        strike = float(strike_str)
        config = premium_tracker_configs['btc_put']
        config.active = True
        config.strike = strike
        symbol = get_btc_symbol(btc_bot, strike, 'put')
        if symbol and symbol in btc_bot.options_prices:
            config.last_ask_price = btc_bot.options_prices[symbol]['ask']
        send_telegram(f"🔔 SYSTEM 5: BTC {strike} PUT TRACKING STARTED (IMMEDIATE ALERTS - NO DELAY)\n\n💰 Initial Ask: ${config.last_ask_price:.2f}\n⚡ Every price change will trigger an immediate alert!\n⏰ Time: {get_ist_time()}")
        return redirect('/?success=BTC+PUT+tracking+started!+(Immediate+alerts)')
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error: {e}")
        return redirect('/?success=Error+starting+tracker')

@app.route('/stop_system5_btc_put')
def stop_system5_btc_put():
    global premium_tracker_configs
    config = premium_tracker_configs['btc_put']
    config.active = False
    config.last_ask_price = 0.0
    send_telegram(f"⏸️ SYSTEM 5: BTC PUT TRACKING STOPPED\n\n⏰ Time: {get_ist_time()}")
    return redirect('/?success=BTC+PUT+tracking+stopped!')

@app.route('/start_system5_eth_call', methods=['POST'])
def start_system5_eth_call():
    global premium_tracker_configs
    try:
        strike_str = request.form.get('strike', '')
        if not strike_str:
            return redirect('/?success=Please+select+a+strike')
        strike = float(strike_str)
        config = premium_tracker_configs['eth_call']
        config.active = True
        config.strike = strike
        symbol = get_eth_symbol(eth_bot, strike, 'call')
        if symbol and symbol in eth_bot.options_prices:
            config.last_ask_price = eth_bot.options_prices[symbol]['ask']
        send_telegram(f"🔔 SYSTEM 5: ETH {strike} CALL TRACKING STARTED (IMMEDIATE ALERTS - NO DELAY)\n\n💰 Initial Ask: ${config.last_ask_price:.2f}\n⚡ Every price change will trigger an immediate alert!\n⏰ Time: {get_ist_time()}")
        return redirect('/?success=ETH+CALL+tracking+started!+(Immediate+alerts)')
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error: {e}")
        return redirect('/?success=Error+starting+tracker')

@app.route('/stop_system5_eth_call')
def stop_system5_eth_call():
    global premium_tracker_configs
    config = premium_tracker_configs['eth_call']
    config.active = False
    config.last_ask_price = 0.0
    send_telegram(f"⏸️ SYSTEM 5: ETH CALL TRACKING STOPPED\n\n⏰ Time: {get_ist_time()}")
    return redirect('/?success=ETH+CALL+tracking+stopped!')

@app.route('/start_system5_eth_put', methods=['POST'])
def start_system5_eth_put():
    global premium_tracker_configs
    try:
        strike_str = request.form.get('strike', '')
        if not strike_str:
            return redirect('/?success=Please+select+a+strike')
        strike = float(strike_str)
        config = premium_tracker_configs['eth_put']
        config.active = True
        config.strike = strike
        symbol = get_eth_symbol(eth_bot, strike, 'put')
        if symbol and symbol in eth_bot.options_prices:
            config.last_ask_price = eth_bot.options_prices[symbol]['ask']
        send_telegram(f"🔔 SYSTEM 5: ETH {strike} PUT TRACKING STARTED (IMMEDIATE ALERTS - NO DELAY)\n\n💰 Initial Ask: ${config.last_ask_price:.2f}\n⚡ Every price change will trigger an immediate alert!\n⏰ Time: {get_ist_time()}")
        return redirect('/?success=ETH+PUT+tracking+started!+(Immediate+alerts)')
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error: {e}")
        return redirect('/?success=Error+starting+tracker')

@app.route('/stop_system5_eth_put')
def stop_system5_eth_put():
    global premium_tracker_configs
    config = premium_tracker_configs['eth_put']
    config.active = False
    config.last_ask_price = 0.0
    send_telegram(f"⏸️ SYSTEM 5: ETH PUT TRACKING STOPPED\n\n⏰ Time: {get_ist_time()}")
    return redirect('/?success=ETH+PUT+tracking+stopped!')

@app.route('/health')
def health():
    current_time_str = get_ist_time()
    
    system5_dict = {}
    for config_id, config in premium_tracker_configs.items():
        system5_dict[config_id] = asdict(config)
    
    return {
        "system_1_arbitrage": {
            "eth": {
                "connected": eth_bot.connected,
                "messages_received": eth_bot.message_count,
                "symbols_tracked": len(eth_bot.options_prices),
                "alerts_sent": eth_bot.alert_count,
                "threshold": DELTA_THRESHOLD['ETH']
            },
            "btc": {
                "running": btc_bot.running,
                "fetch_count": btc_bot.fetch_count,
                "symbols_tracked": len(btc_bot.active_symbols),
                "alerts_sent": btc_bot.alert_count,
                "threshold": DELTA_THRESHOLD['BTC']
            }
        },
        "system_2_option_alerts": {
            "active": new_system_active,
            "configs": {
                config_id: asdict(config) for config_id, config in alert_configs.items()
            }
        },
        "system_3_spike_detector": {
            "condition_1_spike": {
                "active": spike_config.enabled_spike,
                "min_spike_percent": spike_config.min_spike_percent,
                "min_premium": spike_config.spike_min_premium
            },
            "condition_2_spread": {
                "active": spike_config.enabled_spread,
                "min_spread_percent": spike_config.min_spread_percent,
                "min_premium": spike_config.spread_min_premium
            }
        },
        "system_4_premium_match": {
            "active": system4_active,
            "cooldown_seconds": premium_match_config.cooldown_seconds,
            "btc_min_premium": premium_match_config.btc_min_premium,
            "eth_min_premium": premium_match_config.eth_min_premium
        },
        "system_5_premium_tracker": {
            "immediate_alerts": "YES - NO COOLDOWN DELAY",
            "trackers": system5_dict
        },
        "current_time": current_time_str
    }, 200

@app.route('/start_btc')
def start_btc():
    if not btc_bot.running:
        btc_bot.running = True
        threading.Thread(target=btc_bot.start_monitoring, daemon=True).start()
        return "BTC Bot started"
    return "BTC Bot already running"

@app.route('/stop_btc')
def stop_btc():
    btc_bot.stop()
    return "BTC Bot stopped"

@app.route('/ping')
def ping():
    return "pong", 200

# -------------------------------
# Start All Systems
# -------------------------------
def start_bots():
    print("="*60)
    print("QUAD ALERT SYSTEM WITH PREMIUM TRACKER (DARK MODE + IMMEDIATE ALERTS)")
    print("="*60)
    print(f"⚡ System 1: Arbitrage Alerts - ETH: ${DELTA_THRESHOLD['ETH']:.2f}, BTC: ${DELTA_THRESHOLD['BTC']:.2f}")
    print(f"🎯 System 2: Option Strike Alerts")
    print(f"🚨 System 3: Dual Condition Spike Detection")
    print(f"🎯 System 4: Exact Premium Match Detection")
    print(f"⚡ System 5: Premium Tracker (IMMEDIATE ALERTS - NO DELAY)")
    print("="*60)
    
    eth_bot.start()
    btc_thread = threading.Thread(target=btc_bot.start_monitoring, daemon=True)
    btc_thread.start()
    
    print(f"[{datetime.now()}] ✅ All five systems started")
    print(f"[{datetime.now()}] ⚡ System 5: Price change alerts are IMMEDIATE - No cooldown!")

if __name__ == "__main__":
    start_bots()
    sleep(2)
    port = int(os.environ.get("PORT", 10000))
    print(f"[{datetime.now()}] 🌐 Website: http://localhost:{port}")
    print(f"[{datetime.now()}] 🚀 Starting web server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
