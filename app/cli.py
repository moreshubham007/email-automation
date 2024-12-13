import click
from flask.cli import with_appcontext
from app import db
from app.models import User

@click.command('create-user')
@click.argument('username')
@click.argument('email')
@click.argument('password')
@with_appcontext
def create_user(username, email, password):
    """Create a new user."""
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    click.echo(f'Created user: {username}')

def init_app(app):
    app.cli.add_command(create_user) 