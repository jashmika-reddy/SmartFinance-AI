import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from flask import Flask, render_template
from config import Config
from models import db
from currency_utils import format_inr, format_inr_compact, CURRENCY_SYMBOL, CURRENCY_CODE

def create_app(config_class=Config, test_config=None):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    if test_config:
        app.config.update(test_config)
    
    # Initialize Database ORM
    db.init_app(app)
    
    # Register Blueprints
    from routes.auth_routes import auth_bp
    from routes.dashboard_routes import dashboard_bp
    from routes.transaction_routes import transaction_bp
    from routes.budget_routes import budget_bp
    from routes.debt_routes import debt_bp
    from routes.risk_routes import risk_bp
    from routes.advisor_routes import advisor_bp
    from routes.report_routes import report_bp
    from routes.api_routes import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transaction_bp)
    app.register_blueprint(budget_bp)
    app.register_blueprint(debt_bp)
    app.register_blueprint(risk_bp)
    app.register_blueprint(advisor_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(api_bp)

    # Global Context Processor for Currency
    @app.context_processor
    def inject_currency():
        return dict(
            CURRENCY_SYMBOL=CURRENCY_SYMBOL,
            CURRENCY_CODE=CURRENCY_CODE
        )

    # Custom Jinja Filters
    @app.template_filter('currency')
    def currency_filter(val):
        return format_inr(val, decimals=2)

    @app.template_filter('currency_compact')
    def currency_compact_filter(val):
        return format_inr_compact(val)

    @app.template_filter('format_number')
    def format_number(val):
        return format_inr(val, decimals=0, include_symbol=False)

    @app.template_filter('clamp_pct')
    def clamp_pct(val, max_val=100.0):
        try:
            return min(float(max_val), max(0.0, float(val)))
        except (ValueError, TypeError):
            return 0.0

    # Global Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500

    # Ensure DB tables exist
    with app.app_context():
        db.create_all()

    return app

app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print("  SmartFinance AI - Intelligent Personal Financial Risk Management")
    print("  Running on: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)