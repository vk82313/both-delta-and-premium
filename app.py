HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quad Alert System</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            min-height: 100vh;
            padding: 20px;
            color: #e0e0e0;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: #1a1a2e;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            overflow: hidden;
            border: 1px solid #2d2d4a;
        }
        
        .header {
            background: linear-gradient(135deg, #16213e, #0f3460);
            color: #e0e0e0;
            padding: 30px;
            text-align: center;
            border-bottom: 1px solid #2d2d4a;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }
        
        .header .subtitle {
            font-size: 1.2rem;
            opacity: 0.8;
        }
        
        .tabs {
            display: flex;
            background: #0f0f23;
            border-bottom: 2px solid #2d2d4a;
            flex-wrap: wrap;
        }
        
        .tab-btn {
            flex: 1;
            padding: 20px;
            border: none;
            background: none;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            color: #a0a0c0;
        }
        
        .tab-btn:hover {
            background: #1a1a35;
            color: #667eea;
        }
        
        .tab-btn.active {
            background: #1a1a2e;
            color: #667eea;
            border-bottom: 3px solid #667eea;
        }
        
        .tab-content {
            display: none;
            padding: 30px;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .alert-success {
            background: #1a3a2a;
            color: #2ecc71;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            border: 1px solid #2ecc71;
        }
        
        .system-section {
            margin-bottom: 40px;
        }
        
        .section-title {
            font-size: 1.5rem;
            margin-bottom: 20px;
            color: #667eea;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: #0f0f23;
            padding: 25px;
            border-radius: 15px;
            border-left: 5px solid #667eea;
            border: 1px solid #2d2d4a;
        }
        
        .stat-card h3 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.3rem;
        }
        
        .stat-item {
            margin-bottom: 10px;
            font-size: 1.1rem;
            display: flex;
            justify-content: space-between;
        }
        
        .stat-label {
            color: #a0a0c0;
        }
        
        .stat-value {
            font-weight: 600;
            color: #e0e0e0;
        }
        
        .threshold-card {
            background: #0f0f23;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.3);
            margin-bottom: 20px;
            border: 1px solid #2d2d4a;
        }
        
        .threshold-card h3 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.3rem;
        }
        
        .threshold-card h4 {
            color: #e0e0e0;
            margin-bottom: 15px;
        }
        
        .threshold-input {
            width: 100%;
            padding: 12px;
            font-size: 1.1rem;
            border: 2px solid #2d2d4a;
            border-radius: 10px;
            margin-bottom: 15px;
            transition: all 0.3s ease;
            background: #1a1a35;
            color: #e0e0e0;
        }
        
        .threshold-input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
        }
        
        .update-btn {
            padding: 15px 30px;
            font-size: 1.1rem;
            font-weight: 600;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            width: 100%;
        }
        
        .update-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        }
        
        .option-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .option-card {
            background: #0f0f23;
            padding: 25px;
            border-radius: 15px;
            border-top: 5px solid;
            border: 1px solid #2d2d4a;
            border-top-width: 5px;
        }
        
        .btc-call { border-color: #3498db; border-top-color: #3498db; }
        .btc-put { border-color: #e74c3c; border-top-color: #e74c3c; }
        .eth-call { border-color: #2ecc71; border-top-color: #2ecc71; }
        .eth-put { border-color: #9b59b6; border-top-color: #9b59b6; }
        
        .option-card h4 {
            font-size: 1.2rem;
            margin-bottom: 15px;
            color: #e0e0e0;
        }
        
        .select-input {
            width: 100%;
            padding: 12px;
            font-size: 1.1rem;
            border: 2px solid #2d2d4a;
            border-radius: 10px;
            margin-bottom: 15px;
            background: #1a1a35;
            color: #e0e0e0;
        }
        
        .select-input option {
            background: #1a1a35;
            color: #e0e0e0;
        }
        
        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 15px;
        }
        
        .checkbox-group input[type="checkbox"] {
            width: 20px;
            height: 20px;
            cursor: pointer;
            accent-color: #667eea;
        }
        
        .checkbox-group label {
            color: #e0e0e0;
            cursor: pointer;
        }
        
        .activate-btn {
            padding: 20px;
            font-size: 1.3rem;
            font-weight: 700;
            border: none;
            border-radius: 15px;
            cursor: pointer;
            transition: all 0.3s ease;
            background: linear-gradient(135deg, #2ecc71, #27ae60);
            color: white;
            width: 100%;
            margin-top: 20px;
        }
        
        .activate-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 12px 30px rgba(46, 204, 113, 0.4);
        }
        
        .status-panel {
            background: #0f0f23;
            padding: 25px;
            border-radius: 15px;
            margin-top: 30px;
            border: 1px solid #2d2d4a;
        }
        
        .status-panel h3 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.3rem;
        }
        
        .status-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #2d2d4a;
        }
        
        .status-item:last-child {
            border-bottom: none;
        }
        
        .status-label {
            font-size: 1.1rem;
            color: #a0a0c0;
        }
        
        .status-value {
            font-weight: 600;
            font-size: 1.1rem;
        }
        
        .status-active {
            color: #2ecc71;
        }
        
        .status-inactive {
            color: #e74c3c;
        }
        
        .dual-condition-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        @media (max-width: 768px) {
            .dual-condition-grid {
                grid-template-columns: 1fr;
            }
        }
        
        .condition-panel {
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 20px;
        }
        
        .condition-1 {
            background: linear-gradient(135deg, #1a3a5c, #1a2a4a);
            border: 1px solid #3498db;
        }
        
        .condition-2 {
            background: linear-gradient(135deg, #3a1a5c, #2a1a4a);
            border: 1px solid #9b59b6;
        }
        
        .condition-panel h3 {
            color: #e0e0e0;
            margin-bottom: 20px;
            font-size: 1.5rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .condition-status {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding: 15px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
        }
        
        .condition-controls {
            margin-top: 20px;
        }
        
        .control-buttons {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        
        .start-btn {
            padding: 15px;
            font-size: 1.1rem;
            font-weight: 600;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            background: #2ecc71;
            color: white;
            flex: 1;
            transition: all 0.3s ease;
        }
        
        .stop-btn {
            padding: 15px;
            font-size: 1.1rem;
            font-weight: 600;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            background: #e74c3c;
            color: white;
            flex: 1;
            transition: all 0.3s ease;
        }
        
        .start-btn:hover {
            background: #27ae60;
            transform: translateY(-2px);
        }
        
        .stop-btn:hover {
            background: #c0392b;
            transform: translateY(-2px);
        }
        
        .config-section {
            background: #0f0f23;
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 20px;
            border: 1px solid #2d2d4a;
        }
        
        .config-section h4 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.3rem;
        }
        
        .config-section label {
            color: #a0a0c0;
        }
        
        .condition-section {
            background: #1a1a35;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            border-left: 4px solid;
        }
        
        .condition-1-section {
            border-left-color: #3498db;
        }
        
        .condition-2-section {
            border-left-color: #9b59b6;
        }
        
        .condition-section h5 {
            font-size: 1.1rem;
            margin-bottom: 15px;
            color: #e0e0e0;
        }
        
        .condition-section small {
            color: #a0a0c0;
            display: block;
            margin-top: 5px;
            font-size: 0.9rem;
        }
        
        .config-row {
            margin-bottom: 20px;
        }
        
        .config-row label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #a0a0c0;
        }
        
        .checkbox-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-top: 20px;
        }
        
        .save-btn {
            padding: 15px 30px;
            font-size: 1.1rem;
            font-weight: 600;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            background: #3498db;
            color: white;
            width: 100%;
            margin-top: 20px;
        }
        
        .save-btn:hover {
            background: #2980b9;
            transform: translateY(-2px);
        }
        
        .cooldown-note {
            background: rgba(255, 255, 255, 0.1);
            color: #a0a0c0;
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
            font-size: 0.9rem;
            text-align: center;
        }
        
        .system4-panel {
            background: linear-gradient(135deg, #3a2a1a, #2a2a1a);
            border: 1px solid #f39c12;
        }
        
        .cooldown-control {
            display: flex;
            gap: 10px;
            align-items: center;
            justify-content: center;
            margin-top: 15px;
        }
        
        .cooldown-btn {
            padding: 10px 20px;
            font-size: 1.2rem;
            font-weight: bold;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            background: rgba(255, 255, 255, 0.1);
            color: #e0e0e0;
            transition: all 0.3s ease;
        }
        
        .cooldown-btn:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: scale(1.05);
        }
        
        .cooldown-input {
            width: 100px;
            text-align: center;
            padding: 10px;
            font-size: 1.1rem;
            border: 2px solid #2d2d4a;
            border-radius: 8px;
            background: #1a1a35;
            color: #e0e0e0;
            font-weight: bold;
        }
        
        .filter-input {
            width: 150px;
            text-align: center;
            padding: 10px;
            font-size: 1.1rem;
            border: 2px solid #f39c12;
            border-radius: 8px;
            background: #1a1a35;
            color: #e0e0e0;
            font-weight: bold;
        }
        
        .stat-highlight {
            font-size: 1.5rem;
            font-weight: bold;
            color: #f39c12;
        }
        
        .tracker-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .tracker-card {
            background: #0f0f23;
            padding: 25px;
            border-radius: 15px;
            border-top: 5px solid;
            text-align: center;
            border: 1px solid #2d2d4a;
            border-top-width: 5px;
        }
        
        .tracker-card.monitoring {
            background: #1a2a1a;
            box-shadow: 0 0 20px rgba(46, 204, 113, 0.2);
            border-color: #2ecc71;
        }
        
        .tracker-card h4 {
            font-size: 1.3rem;
            margin-bottom: 20px;
            color: #667eea;
        }
        
        .tracker-status {
            font-size: 1.2rem;
            font-weight: 700;
            margin: 15px 0;
        }
        
        .tracker-card p {
            color: #a0a0c0;
            margin: 10px 0;
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            color: #a0a0c0;
            border-top: 1px solid #2d2d4a;
            margin-top: 30px;
        }
        
        .footer a {
            color: #667eea;
            text-decoration: none;
        }
        
        .footer a:hover {
            text-decoration: underline;
        }
        
        @media (max-width: 768px) {
            .header h1 {
                font-size: 2rem;
            }
            
            .tab-btn {
                padding: 15px;
                font-size: 0.9rem;
            }
            
            .tab-content {
                padding: 20px;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .option-section {
                grid-template-columns: 1fr;
            }
            
            .tracker-grid {
                grid-template-columns: 1fr;
            }
            
            .control-buttons {
                flex-direction: column;
            }
            
            .checkbox-grid {
                grid-template-columns: 1fr;
            }
            
            .cooldown-control {
                flex-wrap: wrap;
            }
        }
        
        input, select, textarea {
            color-scheme: dark;
        }
        
        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: #0f0f23;
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #2d2d4a;
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #667eea;
        }
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
        
        <!-- Success Message -->
        {% if success %}
        <div class="alert-success">
            ✅ {{ success }}
        </div>
        {% endif %}
        
        <!-- Tab 1: Arbitrage System -->
        <div id="arbitrage-tab" class="tab-content active">
            <div class="system-section">
                <h2 class="section-title">⚡ Arbitrage Alert System</h2>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>🔵 ETH WebSocket Bot</h3>
                        <div class="stat-item">
                            <span class="stat-label">Status:</span>
                            <span class="stat-value">{{ "✅ Connected" if eth_bot.connected else "🔴 Disconnected" }}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Messages:</span>
                            <span class="stat-value">{{ eth_bot.message_count }}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">ETH Symbols:</span>
                            <span class="stat-value">{{ len(eth_bot.options_prices) }}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Active Expiry:</span>
                            <span class="stat-value">{{ eth_bot.active_expiry }}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">ETH Alerts:</span>
                            <span class="stat-value">{{ eth_bot.alert_count }}</span>
                        </div>
                    </div>
                    
                    <div class="stat-card">
                        <h3>🟠 BTC REST API Bot</h3>
                        <div class="stat-item">
                            <span class="stat-label">Status:</span>
                            <span class="stat-value">{{ "✅ Running" if btc_bot.running else "🔴 Stopped" }}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Fetches:</span>
                            <span class="stat-value">{{ btc_bot.fetch_count }}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">BTC Symbols:</span>
                            <span class="stat-value">{{ len(btc_bot.active_symbols) }}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Active Expiry:</span>
                            <span class="stat-value">{{ btc_bot.active_expiry }}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">BTC Alerts:</span>
                            <span class="stat-value">{{ btc_bot.alert_count }}</span>
                        </div>
                    </div>
                </div>
                
                <div class="threshold-card">
                    <h3>⚙️ Update Arbitrage Thresholds</h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                        <div>
                            <h4>ETH Threshold: ${{ "%.2f"|format(DELTA_THRESHOLD['ETH']) }}</h4>
                            <form action="/update_eth_threshold" method="POST">
                                <input type="number" name="threshold" value="{{ "%.2f"|format(DELTA_THRESHOLD['ETH']) }}" 
                                       step="0.01" min="0.01" max="10" class="threshold-input" required>
                                <button type="submit" class="update-btn">Update ETH Threshold</button>
                            </form>
                        </div>
                        <div>
                            <h4>BTC Threshold: ${{ "%.2f"|format(DELTA_THRESHOLD['BTC']) }}</h4>
                            <form action="/update_btc_threshold" method="POST">
                                <input type="number" name="threshold" value="{{ "%.2f"|format(DELTA_THRESHOLD['BTC']) }}" 
                                       step="0.01" min="0.01" max="50" class="threshold-input" required>
                                <button type="submit" class="update-btn">Update BTC Threshold</button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Tab 2: Option Alerts System -->
        <div id="option-alerts-tab" class="tab-content">
            <div class="system-section">
                <h2 class="section-title">🎯 Option Strike Alert System</h2>
                <p style="margin-bottom: 20px; color: #a0a0c0;">Configure alerts for specific strikes and premiums</p>
                
                <form action="/activate_alerts" method="POST">
                    <div class="option-section">
                        <div class="option-card btc-call">
                            <h4>🔵 BTC CALL OPTIONS</h4>
                            <select name="btc_call_strike" class="select-input">
                                <option value="">Select Strike</option>
                                {% for strike in btc_bot.option_chain_data.calls.keys()|sort %}
                                <option value="{{ strike }}" {% if alert_configs['btc_call'].strike == strike %}selected{% endif %}>
                                    {{ strike }}
                                </option>
                                {% endfor %}
                            </select>
                            <input type="number" name="btc_call_premium" placeholder="Premium ($)" 
                                   value="{{ "%.2f"|format(alert_configs['btc_call'].premium) if alert_configs['btc_call'].premium > 0 else '' }}"
                                   step="0.01" min="0" class="threshold-input">
                            <div class="checkbox-group">
                                <input type="checkbox" name="btc_call_monitor" id="btc_call_monitor" 
                                       {% if alert_configs['btc_call'].is_monitoring %}checked{% endif %}>
                                <label for="btc_call_monitor">Monitor BTC Calls</label>
                            </div>
                        </div>
                        
                        <div class="option-card btc-put">
                            <h4>🔴 BTC PUT OPTIONS</h4>
                            <select name="btc_put_strike" class="select-input">
                                <option value="">Select Strike</option>
                                {% for strike in btc_bot.option_chain_data.puts.keys()|sort %}
                                <option value="{{ strike }}" {% if alert_configs['btc_put'].strike == strike %}selected{% endif %}>
                                    {{ strike }}
                                </option>
                                {% endfor %}
                            </select>
                            <input type="number" name="btc_put_premium" placeholder="Premium ($)" 
                                   value="{{ "%.2f"|format(alert_configs['btc_put'].premium) if alert_configs['btc_put'].premium > 0 else '' }}"
                                   step="0.01" min="0" class="threshold-input">
                            <div class="checkbox-group">
                                <input type="checkbox" name="btc_put_monitor" id="btc_put_monitor"
                                       {% if alert_configs['btc_put'].is_monitoring %}checked{% endif %}>
                                <label for="btc_put_monitor">Monitor BTC Puts</label>
                            </div>
                        </div>
                        
                        <div class="option-card eth-call">
                            <h4>🟢 ETH CALL OPTIONS</h4>
                            <select name="eth_call_strike" class="select-input">
                                <option value="">Select Strike</option>
                                {% for strike in eth_bot.option_chain_data.calls.keys()|sort %}
                                <option value="{{ strike }}" {% if alert_configs['eth_call'].strike == strike %}selected{% endif %}>
                                    {{ strike }}
                                </option>
                                {% endfor %}
                            </select>
                            <input type="number" name="eth_call_premium" placeholder="Premium ($)" 
                                   value="{{ "%.2f"|format(alert_configs['eth_call'].premium) if alert_configs['eth_call'].premium > 0 else '' }}"
                                   step="0.01" min="0" class="threshold-input">
                            <div class="checkbox-group">
                                <input type="checkbox" name="eth_call_monitor" id="eth_call_monitor"
                                       {% if alert_configs['eth_call'].is_monitoring %}checked{% endif %}>
                                <label for="eth_call_monitor">Monitor ETH Calls</label>
                            </div>
                        </div>
                        
                        <div class="option-card eth-put">
                            <h4>🟣 ETH PUT OPTIONS</h4>
                            <select name="eth_put_strike" class="select-input">
                                <option value="">Select Strike</option>
                                {% for strike in eth_bot.option_chain_data.puts.keys()|sort %}
                                <option value="{{ strike }}" {% if alert_configs['eth_put'].strike == strike %}selected{% endif %}>
                                    {{ strike }}
                                </option>
                                {% endfor %}
                            </select>
                            <input type="number" name="eth_put_premium" placeholder="Premium ($)" 
                                   value="{{ "%.2f"|format(alert_configs['eth_put'].premium) if alert_configs['eth_put'].premium > 0 else '' }}"
                                   step="0.01" min="0" class="threshold-input">
                            <div class="checkbox-group">
                                <input type="checkbox" name="eth_put_monitor" id="eth_put_monitor"
                                       {% if alert_configs['eth_put'].is_monitoring %}checked{% endif %}>
                                <label for="eth_put_monitor">Monitor ETH Puts</label>
                            </div>
                        </div>
                    </div>
                    
                    <button type="submit" class="activate-btn">🚀 ACTIVATE ALERTS</button>
                </form>
                
                <div class="status-panel">
                    <h3>📊 Active Alerts Status</h3>
                    <div class="status-item">
                        <span class="status-label">BTC Calls:</span>
                        <span class="status-value {% if alert_configs['btc_call'].is_monitoring %}status-active{% else %}status-inactive{% endif %}">
                            {% if alert_configs['btc_call'].is_monitoring %}✅ ACTIVE{% else %}❌ INACTIVE{% endif %}
                        </span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">BTC Puts:</span>
                        <span class="status-value {% if alert_configs['btc_put'].is_monitoring %}status-active{% else %}status-inactive{% endif %}">
                            {% if alert_configs['btc_put'].is_monitoring %}✅ ACTIVE{% else %}❌ INACTIVE{% endif %}
                        </span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">ETH Calls:</span>
                        <span class="status-value {% if alert_configs['eth_call'].is_monitoring %}status-active{% else %}status-inactive{% endif %}">
                            {% if alert_configs['eth_call'].is_monitoring %}✅ ACTIVE{% else %}❌ INACTIVE{% endif %}
                        </span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">ETH Puts:</span>
                        <span class="status-value {% if alert_configs['eth_put'].is_monitoring %}status-active{% else %}status-inactive{% endif %}">
                            {% if alert_configs['eth_put'].is_monitoring %}✅ ACTIVE{% else %}❌ INACTIVE{% endif %}
                        </span>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Tab 3: Premium Spike Detector -->
        <div id="spike-detector-tab" class="tab-content">
            <div class="system-section">
                <h2 class="section-title">🚨 DUAL CONDITION SPIKE DETECTOR</h2>
                
                <div class="dual-condition-grid">
                    <div class="condition-panel condition-1">
                        <h3>📊 CONDITION 1: PRICE SPIKE</h3>
                        <div class="condition-status">
                            <div>
                                <strong>Status:</strong>
                                <span style="color: {% if spike_config.enabled_spike %}#2ecc71{% else %}#e74c3c{% endif %}; font-weight: bold;">
                                    {% if spike_config.enabled_spike %}🟢 RUNNING{% else %}🔴 STOPPED{% endif %}
                                </span>
                            </div>
                        </div>
                        <div class="condition-controls">
                            <form action="/start_spike_detection" method="POST" style="margin-bottom: 10px;">
                                <button type="submit" class="start-btn">▶️ START SPIKE</button>
                            </form>
                            <form action="/stop_spike_detection" method="POST">
                                <button type="submit" class="stop-btn">⏸️ STOP SPIKE</button>
                            </form>
                        </div>
                    </div>
                    
                    <div class="condition-panel condition-2">
                        <h3>📊 CONDITION 2: BID-ASK SPREAD</h3>
                        <div class="condition-status">
                            <div>
                                <strong>Status:</strong>
                                <span style="color: {% if spike_config.enabled_spread %}#2ecc71{% else %}#e74c3c{% endif %}; font-weight: bold;">
                                    {% if spike_config.enabled_spread %}🟢 RUNNING{% else %}🔴 STOPPED{% endif %}
                                </span>
                            </div>
                        </div>
                        <div class="condition-controls">
                            <form action="/start_spread_detection" method="POST" style="margin-bottom: 10px;">
                                <button type="submit" class="start-btn">▶️ START SPREAD</button>
                            </form>
                            <form action="/stop_spread_detection" method="POST">
                                <button type="submit" class="stop-btn">⏸️ STOP SPREAD</button>
                            </form>
                        </div>
                    </div>
                </div>
                
                <div class="config-section">
                    <h4>Configuration Settings</h4>
                    <form action="/update_spike_config" method="POST">
                        <div class="condition-section condition-1-section">
                            <h5>📊 CONDITION 1: PRICE SPIKE</h5>
                            <div class="config-row">
                                <label for="min_spike_percent">Minimum Spike Percentage:</label>
                                <input type="number" id="min_spike_percent" name="min_spike_percent" 
                                       value="{{ spike_config.min_spike_percent }}" step="0.1"
                                       class="threshold-input" required>
                                <small>Alert when bid price increases by this percentage (100% = price doubles)</small>
                            </div>
                            <div class="config-row">
                                <label for="spike_min_premium">Minimum Premium Filter:</label>
                                <input type="number" id="spike_min_premium" name="spike_min_premium" 
                                       value="{{ spike_config.spike_min_premium }}" step="0.01" min="0"
                                       class="threshold-input" required>
                                <small>Only check spikes for options with bid price ≥ this amount ($)</small>
                            </div>
                        </div>
                        
                        <div class="condition-section condition-2-section">
                            <h5>📊 CONDITION 2: BID-ASK SPREAD</h5>
                            <div class="config-row">
                                <label for="min_spread_percent">Minimum Spread Percentage:</label>
                                <input type="number" id="min_spread_percent" name="min_spread_percent" 
                                       value="{{ spike_config.min_spread_percent }}" step="0.1"
                                       class="threshold-input" required>
                                <small>Alert when (Ask-Bid)/Bid × 100 ≥ this percentage (100% = ask is double the bid)</small>
                            </div>
                            <div class="config-row">
                                <label for="spread_min_premium">Minimum Premium Filter:</label>
                                <input type="number" id="spread_min_premium" name="spread_min_premium" 
                                       value="{{ spike_config.spread_min_premium }}" step="0.01" min="0"
                                       class="threshold-input" required>
                                <small>Only check spreads for options with bid price ≥ this amount ($)</small>
                            </div>
                        </div>
                        
                        <div class="checkbox-grid">
                            <div class="checkbox-group">
                                <input type="checkbox" id="monitor_eth" name="monitor_eth" 
                                       {% if spike_config.monitor_eth %}checked{% endif %}>
                                <label for="monitor_eth">Monitor ETH</label>
                            </div>
                            <div class="checkbox-group">
                                <input type="checkbox" id="monitor_btc" name="monitor_btc"
                                       {% if spike_config.monitor_btc %}checked{% endif %}>
                                <label for="monitor_btc">Monitor BTC</label>
                            </div>
                            <div class="checkbox-group">
                                <input type="checkbox" id="monitor_calls" name="monitor_calls"
                                       {% if spike_config.monitor_calls %}checked{% endif %}>
                                <label for="monitor_calls">Include Calls</label>
                            </div>
                            <div class="checkbox-group">
                                <input type="checkbox" id="monitor_puts" name="monitor_puts"
                                       {% if spike_config.monitor_puts %}checked{% endif %}>
                                <label for="monitor_puts">Include Puts</label>
                            </div>
                        </div>
                        
                        <button type="submit" class="save-btn">💾 SAVE SETTINGS</button>
                    </form>
                </div>
            </div>
        </div>
        
        <!-- Tab 4: Premium Match Detector -->
        <div id="premium-match-tab" class="tab-content">
            <div class="system-section">
                <h2 class="section-title">🎯 EXACT PREMIUM MATCH DETECTOR</h2>
                
                <div class="condition-panel system4-panel">
                    <h3>📊 SYSTEM 4 STATUS</h3>
                    
                    <div class="condition-status">
                        <div>
                            <strong>Status:</strong>
                            <span style="color: {% if system4_active %}#2ecc71{% else %}#e74c3c{% endif %}; font-weight: bold;">
                                {% if system4_active %}🟢 RUNNING{% else %}🔴 STOPPED{% endif %}
                            </span>
                        </div>
                    </div>
                    
                    <div class="condition-controls" style="display: flex; gap: 15px; margin-top: 20px;">
                        <form action="/start_system4" method="POST" style="flex: 1;">
                            <button type="submit" class="start-btn" style="background: #2ecc71; width: 100%;">
                                ▶️ START SYSTEM 4
                            </button>
                        </form>
                        <form action="/stop_system4" method="POST" style="flex: 1;">
                            <button type="submit" class="stop-btn" style="background: #e74c3c; width: 100%;">
                                ⏸️ STOP SYSTEM 4
                            </button>
                        </form>
                    </div>
                </div>
                
                <div class="config-section" style="margin-top: 20px;">
                    <h4>⚙️ COOLDOWN CONFIGURATION</h4>
                    <form action="/update_system4_cooldown" method="POST">
                        <div class="config-row">
                            <label for="cooldown_seconds">Cooldown Duration (seconds):</label>
                            <div class="cooldown-control">
                                <button type="button" onclick="decrementCooldown()" class="cooldown-btn">-</button>
                                <input type="number" id="cooldown_seconds" name="cooldown_seconds" 
                                       value="{{ premium_match_config.cooldown_seconds }}" 
                                       step="5" min="5" max="300"
                                       class="cooldown-input">
                                <button type="button" onclick="incrementCooldown()" class="cooldown-btn">+</button>
                                <span style="margin-left: 10px;">seconds</span>
                            </div>
                        </div>
                        <button type="submit" class="save-btn" style="background: #f39c12; margin-top: 20px;">💾 UPDATE COOLDOWN</button>
                    </form>
                </div>
                
                <div class="config-section" style="margin-top: 20px;">
                    <h4>💰 BTC PREMIUM FILTER</h4>
                    <form action="/update_system4_btc_filter" method="POST">
                        <div class="config-row">
                            <label for="btc_min_premium">BTC Minimum Premium ($):</label>
                            <div class="cooldown-control">
                                <button type="button" onclick="decrementBtcFilter()" class="cooldown-btn" style="background: #f39c12;">-</button>
                                <input type="number" id="btc_min_premium" name="btc_min_premium" 
                                       value="{{ premium_match_config.btc_min_premium }}" 
                                       step="0.5" min="0" max="1000"
                                       class="filter-input">
                                <button type="button" onclick="incrementBtcFilter()" class="cooldown-btn" style="background: #f39c12;">+</button>
                            </div>
                        </div>
                        <button type="submit" class="save-btn" style="background: #e67e22; margin-top: 20px;">💾 UPDATE BTC FILTER</button>
                    </form>
                </div>
                
                <div class="config-section" style="margin-top: 20px;">
                    <h4>💰 ETH PREMIUM FILTER</h4>
                    <form action="/update_system4_eth_filter" method="POST">
                        <div class="config-row">
                            <label for="eth_min_premium">ETH Minimum Premium ($):</label>
                            <div class="cooldown-control">
                                <button type="button" onclick="decrementEthFilter()" class="cooldown-btn" style="background: #f39c12;">-</button>
                                <input type="number" id="eth_min_premium" name="eth_min_premium" 
                                       value="{{ premium_match_config.eth_min_premium }}" 
                                       step="0.5" min="0" max="500"
                                       class="filter-input">
                                <button type="button" onclick="incrementEthFilter()" class="cooldown-btn" style="background: #f39c12;">+</button>
                            </div>
                        </div>
                        <button type="submit" class="save-btn" style="background: #e67e22; margin-top: 20px;">💾 UPDATE ETH FILTER</button>
                    </form>
                </div>
            </div>
        </div>
        
        <!-- Tab 5: Premium Tracker (System 5) -->
        <div id="premium-tracker-tab" class="tab-content">
            <div class="system-section">
                <h2 class="section-title">🎯 PREMIUM TRACKER</h2>
                <p style="margin-bottom: 20px; color: #a0a0c0;">Monitor ask price changes for specific contracts</p>
                
                <div class="tracker-grid">
                    <!-- BTC CALL -->
                    <div class="tracker-card btc-call {% if premium_tracker_configs['btc_call'].active %}monitoring{% endif %}">
                        <h4>🔵 BTC CALL</h4>
                        <form action="/start_system5_btc_call" method="POST">
                            <select name="strike" class="select-input" {% if premium_tracker_configs['btc_call'].active %}disabled{% endif %}>
                                <option value="">Select Strike</option>
                                {% for strike in btc_bot.option_chain_data.calls.keys()|sort %}
                                <option value="{{ strike }}" {% if premium_tracker_configs['btc_call'].strike == strike %}selected{% endif %}>
                                    {{ strike }}
                                </option>
                                {% endfor %}
                            </select>
                            {% if premium_tracker_configs['btc_call'].active %}
                            <p>Last Ask: ${{ "%.2f"|format(premium_tracker_configs['btc_call'].last_ask_price) }}</p>
                            <p class="tracker-status status-active">🟢 MONITORING</p>
                            <button type="button" class="stop-btn" onclick="location.href='/stop_system5_btc_call'" style="width:100%;">⏸️ STOP</button>
                            {% else %}
                            <p>Last Ask: --</p>
                            <p class="tracker-status status-inactive">🔴 INACTIVE</p>
                            <button type="submit" class="start-btn" style="width:100%;">▶️ START</button>
                            {% endif %}
                        </form>
                    </div>
                    
                    <!-- BTC PUT -->
                    <div class="tracker-card btc-put {% if premium_tracker_configs['btc_put'].active %}monitoring{% endif %}">
                        <h4>🔴 BTC PUT</h4>
                        <form action="/start_system5_btc_put" method="POST">
                            <select name="strike" class="select-input" {% if premium_tracker_configs['btc_put'].active %}disabled{% endif %}>
                                <option value="">Select Strike</option>
                                {% for strike in btc_bot.option_chain_data.puts.keys()|sort %}
                                <option value="{{ strike }}" {% if premium_tracker_configs['btc_put'].strike == strike %}selected{% endif %}>
                                    {{ strike }}
                                </option>
                                {% endfor %}
                            </select>
                            {% if premium_tracker_configs['btc_put'].active %}
                            <p>Last Ask: ${{ "%.2f"|format(premium_tracker_configs['btc_put'].last_ask_price) }}</p>
                            <p class="tracker-status status-active">🟢 MONITORING</p>
                            <button type="button" class="stop-btn" onclick="location.href='/stop_system5_btc_put'" style="width:100%;">⏸️ STOP</button>
                            {% else %}
                            <p>Last Ask: --</p>
                            <p class="tracker-status status-inactive">🔴 INACTIVE</p>
                            <button type="submit" class="start-btn" style="width:100%;">▶️ START</button>
                            {% endif %}
                        </form>
                    </div>
                    
                    <!-- ETH CALL -->
                    <div class="tracker-card eth-call {% if premium_tracker_configs['eth_call'].active %}monitoring{% endif %}">
                        <h4>🟢 ETH CALL</h4>
                        <form action="/start_system5_eth_call" method="POST">
                            <select name="strike" class="select-input" {% if premium_tracker_configs['eth_call'].active %}disabled{% endif %}>
                                <option value="">Select Strike</option>
                                {% for strike in eth_bot.option_chain_data.calls.keys()|sort %}
                                <option value="{{ strike }}" {% if premium_tracker_configs['eth_call'].strike == strike %}selected{% endif %}>
                                    {{ strike }}
                                </option>
                                {% endfor %}
                            </select>
                            {% if premium_tracker_configs['eth_call'].active %}
                            <p>Last Ask: ${{ "%.2f"|format(premium_tracker_configs['eth_call'].last_ask_price) }}</p>
                            <p class="tracker-status status-active">🟢 MONITORING</p>
                            <button type="button" class="stop-btn" onclick="location.href='/stop_system5_eth_call'" style="width:100%;">⏸️ STOP</button>
                            {% else %}
                            <p>Last Ask: --</p>
                            <p class="tracker-status status-inactive">🔴 INACTIVE</p>
                            <button type="submit" class="start-btn" style="width:100%;">▶️ START</button>
                            {% endif %}
                        </form>
                    </div>
                    
                    <!-- ETH PUT -->
                    <div class="tracker-card eth-put {% if premium_tracker_configs['eth_put'].active %}monitoring{% endif %}">
                        <h4>🟣 ETH PUT</h4>
                        <form action="/start_system5_eth_put" method="POST">
                            <select name="strike" class="select-input" {% if premium_tracker_configs['eth_put'].active %}disabled{% endif %}>
                                <option value="">Select Strike</option>
                                {% for strike in eth_bot.option_chain_data.puts.keys()|sort %}
                                <option value="{{ strike }}" {% if premium_tracker_configs['eth_put'].strike == strike %}selected{% endif %}>
                                    {{ strike }}
                                </option>
                                {% endfor %}
                            </select>
                            {% if premium_tracker_configs['eth_put'].active %}
                            <p>Last Ask: ${{ "%.2f"|format(premium_tracker_configs['eth_put'].last_ask_price) }}</p>
                            <p class="tracker-status status-active">🟢 MONITORING</p>
                            <button type="button" class="stop-btn" onclick="location.href='/stop_system5_eth_put'" style="width:100%;">⏸️ STOP</button>
                            {% else %}
                            <p>Last Ask: --</p>
                            <p class="tracker-status status-inactive">🔴 INACTIVE</p>
                            <button type="submit" class="start-btn" style="width:100%;">▶️ START</button>
                            {% endif %}
                        </form>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Auto-expiry at 5:30 PM IST • All systems running simultaneously</p>
            <p>Last Update: {{ get_ist_time() }} • <a href="/health">Health Check</a></p>
        </div>
    </div>
    
    <script>
        function showTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            document.getElementById(tabName + '-tab').classList.add('active');
            event.target.classList.add('active');
        }
        
        function decrementCooldown() {
            let input = document.getElementById('cooldown_seconds');
            let currentValue = parseInt(input.value);
            if (currentValue > 5) {
                input.value = currentValue - 5;
            }
        }
        
        function incrementCooldown() {
            let input = document.getElementById('cooldown_seconds');
            let currentValue = parseInt(input.value);
            if (currentValue < 300) {
                input.value = currentValue + 5;
            }
        }
        
        function decrementBtcFilter() {
            let input = document.getElementById('btc_min_premium');
            let currentValue = parseFloat(input.value);
            if (currentValue >= 0.5) {
                input.value = (currentValue - 0.5).toFixed(1);
            } else if (currentValue > 0 && currentValue < 0.5) {
                input.value = 0;
            }
        }
        
        function incrementBtcFilter() {
            let input = document.getElementById('btc_min_premium');
            let currentValue = parseFloat(input.value);
            if (currentValue <= 999.5) {
                input.value = (currentValue + 0.5).toFixed(1);
            }
        }
        
        function decrementEthFilter() {
            let input = document.getElementById('eth_min_premium');
            let currentValue = parseFloat(input.value);
            if (currentValue >= 0.5) {
                input.value = (currentValue - 0.5).toFixed(1);
            } else if (currentValue > 0 && currentValue < 0.5) {
                input.value = 0;
            }
        }
        
        function incrementEthFilter() {
            let input = document.getElementById('eth_min_premium');
            let currentValue = parseFloat(input.value);
            if (currentValue <= 499.5) {
                input.value = (currentValue + 0.5).toFixed(1);
            }
        }
        
        setTimeout(function() {
            window.location.reload();
        }, 30000);
    </script>
</body>
</html>
'''
