import click

from src.extensions import db
from src.models import Stock

# Large ASX companies, so search and the dashboard have something to show on a fresh install
ASX_STOCKS = [
    ("BHP.AX", "BHP Group Limited"),
    ("CBA.AX", "Commonwealth Bank of Australia"),
    ("CSL.AX", "CSL Limited"),
    ("NAB.AX", "National Australia Bank Limited"),
    ("WBC.AX", "Westpac Banking Corporation"),
    ("ANZ.AX", "ANZ Group Holdings Limited"),
    ("WOW.AX", "Woolworths Group Limited"),
    ("TLS.AX", "Telstra Group Limited"),
    ("RIO.AX", "Rio Tinto Limited"),
    ("FMG.AX", "Fortescue Ltd"),
]


def register_commands(app):
    @app.cli.command("seed-stocks")
    def seed_stocks():
        """Add a starter set of large ASX companies to the stocks table."""
        existing = {symbol for (symbol,) in db.session.query(Stock.symbol)}
        new_stocks = [
            Stock(symbol=symbol, name=name, exchange="ASX") for symbol, name in ASX_STOCKS if symbol not in existing
        ]
        db.session.add_all(new_stocks)
        db.session.commit()
        click.echo(f"Added {len(new_stocks)} stocks ({len(ASX_STOCKS) - len(new_stocks)} already present).")
