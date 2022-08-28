#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import datetime
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from config import Config
from models import Venue, Show, Artist, db
from flask_migrate import Migrate
import traceback
import psycopg2

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object(Config)
migrate = Migrate(app, db)
db.init_app(app)

# with app.app_context():
#      db.create_all()
# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

# TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format="EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format="EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    venues= Venue.query.all()
    states= set()
    cities= set()
    combinations = set()
    data=[]

    for venue in venues:
        states.add(venue.state)
        cities.add(venue.city)
        combination = (venue.state, venue.city)
        combinations.add(combination)
    combinations = list(combinations)

    for combination in sorted(combinations):
        venue_info = []
        for venue in venues:
            shows_for_venue = Show.query.filter_by(venue_id=venue.id).all()
            if shows_for_venue:
                num_upcoming_shows=len([show for show in shows_for_venue if show.start_time > datetime.now()])
            else:
                num_upcoming_shows = 0

            if (venue.state, venue.city) == combination:
                venue_details = {
                'id':venue.id,
                'name': venue.name,
                'num_upcoming_shows': num_upcoming_shows
                }

                venue_info.append(venue_details)

        data.append({"city":combination[1], "state":combination[0], "venues": venue_info})
    return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    chars = request.form.get('search_term').lower()
    result = []
    data = []

    for venue in Venue.query.all():
        if chars in venue.name.lower():
            result.append(venue.name)
            venue_shows = Show.query.filter_by(venue_id=venue.id)
            num_upcoming_shows= len([show for show in venue_shows if show.start_time > datetime.now()])
            info = dict()
            info['id'] = venue.id
            info['name'] = venue.name
            info["num_upcoming_shows"] = num_upcoming_shows
            data.append(info)

    response={
        "count": len(data),
        "data": data
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    venue = Venue.query.get(venue_id)

    venue_shows = Show.query.filter_by(venue_id=venue_id).all()
    past_shows = []
    upcoming_shows = []

    for show in venue_shows:
        artist = Artist.query.get(show.artist_id)
        show_info = {
            'artist_id': show.artist_id,
            'artist_name': artist.name,
            'artist_image_link': artist.image_link,
            'start_time': str(show.start_time)
        }

        if show.start_time > datetime.now():
            upcoming_shows.append(show_info)
        else:
            past_shows.append(show_info)

    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres.split(','),
        "city": venue.city,
        "state": venue.state,
        "address": venue.address,
        "phone": venue.phone,
        'website': venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "image_link": venue.image_link,
        "seeking_description": venue.seeking_description,
        "past_shows": past_shows,
        "upcoming_shows":upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
      }

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET', 'POST'])
def create_venue_form():
    try:
        if request.method == 'GET':
            form = VenueForm()
            return render_template('forms/new_venue.html', form=form)
        elif request.method == 'POST':
            name = request.form.get('name')
            city = request.form.get('city')
            state = request.form.get('state')
            address = request.form.get('address')
            phone = request.form.get('phone')
            genres = request.form.getlist('genres')
            fb = request.form.get('facebook_link')
            img = request.form.get('image_link')

            if request.form.get('seeking_talent') == 'y':
                seeking_talent = True
            else:
                seeking_talent=False

            seeking_description = request.form.get('seeking_description')
            website = request.form.get('website_link')

            venue_info = Venue(name=name, city=city, state=state, address=address,
            genres=genres, image_link=img, seeking_talent=seeking_talent,
            seeking_description=seeking_description, phone=phone, facebook_link=fb, website=website)

            db.session.add(venue_info)
            db.session.commit()

          # on successful db insert, flash success
            flash(f"{request.form['name']} was successfully listed!")
      # TODO: on unsuccessful db insert, flash an error instead.
    except Exception as e:
        traceback.print_exc()
        db.session.rollback()
        if e.orig.pgcode:
            if e.orig.pgcode == '23505': # psycopg2 UniqueViolation
                flash('An error occurred during listing. Phone number already in records.')
            else:
                flash('An error occurred during listing')
        else:
            flash('An error occurred during listing')

    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion

    return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    try:
        venue = Venue.query.get(venue_id)
        if venue:
            v = venue.name
            db.session.delete(venue)
            db.session.commit()
            flash(f'{v} successfully deleted')
        else:
            flash(f'Venue with id {venue_id} does not exist')
    except:
        traceback.print_exc()
        flash('An error occured. Unable to delete Venue')

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    artists = Artist.query.all()
    data=[]

    for artist in artists:
        artist_info=dict()
        artist_info['id'] = artist.id
        artist_info['name'] = artist.name
        data.append(artist_info)

    return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    chars = request.form.get('search_term').lower()
    result = []
    data = []

    for artist in Artist.query.all():
        if chars in artist.name.lower():
            result.append(artist.name)
            artist_shows = Show.query.filter_by(artist_id=artist.id)
            num_upcoming_shows= len([show for show in artist_shows if show.start_time > datetime.now()])
            info = dict()
            info['id'] = artist.id
            info['name'] = artist.name
            info["num_upcoming_shows"] = num_upcoming_shows
            data.append(info)

    response={
        "count": len(result),
        "data": data
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id

    artist_info = Artist.query.get(artist_id)

    artist_shows = Show.query.filter_by(artist_id=artist_id).all()
    past_shows = []
    upcoming_shows = []

    for show in artist_shows:
        venue = Venue.query.get(show.venue_id)
        show_data = {
          'venue_id': show.venue_id,
          'venue_name': venue.name,
          'venue_image_link': venue.image_link,
          'start_time': str(show.start_time)
        }

        if show.start_time > datetime.now():
            upcoming_shows.append(show_data)
        else:
            past_shows.append(show_data)

    data = {
        "id": artist_id,
        "name": artist_info.name,
        "genres": artist_info.genres.split(','),
        "city": artist_info.city,
        "state": artist_info.state,
        "phone": artist_info.phone,
        'website': artist_info.website,
        "facebook_link": artist_info.facebook_link,
        "seeking_venue": artist_info.seeking_venue,
        "image_link": artist_info.image_link,
        "seeking_description": artist_info.seeking_description,
        "past_shows": past_shows,
        "upcoming_shows":upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
      }

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id)
    form = ArtistForm()
    form.name.data = artist.name
    form.city.data = artist.city
    form.state.data = artist.state
    form.genres.data = artist.genres
    form.phone.data = artist.phone
    form.facebook_link.data = artist.facebook_link
    form.website_link.data = artist.website
    form.image_link.data = artist.image_link
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description


    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    try:
          form=ArtistForm()
          artist = Artist.query.get(artist_id)
          artist.name = request.form['name']
          artist.city = request.form['city']
          artist.state= request.form['state']
          artist.address = request.form.get('address')
          artist.genres = request.form.getlist('genres')
          artist.image_link = request.form.get('image_link')

          if request.form.get('seeking_venue') == 'y':
              artist.seeking_venue = True
          else:
              artist.seeking_venue = False

          artist.seeking_description = request.form.get('seeking_description')
          artist.facebook_link = request.form.get('facebook_link')
          artist.phone = request.form.get('phone')
          artist.website = request.form.get('website_link')

          db.session.commit()
          flash(f'Edit on {artist.name} was successful')

    except:
          traceback.print_exc()
          flash(f'An error occured during editing of {artist.name}')

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)

    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data = venue.state
    form.address.data = venue.address
    form.genres.data = venue.genres
    form.phone.data = venue.phone
    form.facebook_link.data = venue.facebook_link
    form.website_link.data = venue.website
    form.image_link.data = venue.image_link
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description

    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    try:
        venue = Venue.query.get(venue_id)
        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state= request.form['state']
        venue.address = request.form.get('address')
        venue.genres = request.form.getlist('genres')
        venue.image_link = request.form.get('image_link')

        if request.form.get('seeking_talent') == 'y':
            venue.seeking_talent = True
        else:
            venue.seeking_talent = False

        venue.seeking_description = request.form.get('seeking_description')
        venue.facebook_link = request.form.get('facebook_link')
        venue.phone = request.form.get('phone')
        venue.website = request.form.get('website_link')

        db.session.commit()
        flash(f'Edit on {venue.name} was successful')
    except:
        traceback.print_exc()
        flash(f'An error occured during editing of {venue.name}')

    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['POST','GET'])
# called upon submitting the new artist listing form
def create_artist_form(): 
    try:
        if request.method == 'GET':
            form = ArtistForm()
            return render_template('forms/new_artist.html', form=form)

        elif request.method == 'POST':
            name = request.form.get('name')
            city = request.form.get('city')
            state= request.form.get('state')
            phone = request.form.get('phone')
            genres = request.form.getlist('genres')
            fb = request.form.get('facebook_link')
            img = request.form.get('image_link')

            if request.form.get('seeking_venue') == 'y':
                seeking_venue=True
            else:
                seeking_venue=False

            seeking_description=request.form.get('seeking_description')
            web = request.form.get('website_link')

            new_artist = Artist(name=name, city=city, state=state, phone=phone,
            genres=genres, image_link=img, seeking_venue=seeking_venue,
            seeking_description=seeking_description, facebook_link=fb, website=web)

            db.session.add(new_artist)
            db.session.commit()

            #on successful db insert, flash success
            flash(f"Artist {request.form['name']} was successfully listed!")
        # TODO: on unsuccessful db insert, flash an error instead.
    except Exception as e:
        traceback.print_exc()
        db.session.rollback()
        if e.orig.pgcode:
            if e.orig.pgcode == '23505': # psycopg2 UniqueViolation
                flash('An error occurred during listing. Phone number already in records.')
            else:
                flash('An error occurred during listing')
        else:
            flash('An error occurred during listing')

    return render_template('pages/home.html')

  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion'''



#  Shows
#  ----------------------------------------------------------------
@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    shows = Show.query.all()
    data = []

    for show in shows:
        show_info=dict()
        show_info['venue_id'] = show.venue_id
        show_info['venue_name'] = Venue.query.get(show.venue_id).name
        show_info['artist_id'] = show.artist_id
        show_info['artist_name'] = Artist.query.get(show.artist_id).name
        show_info['artist_image_link'] = Artist.query.get(show.artist_id).image_link
        show_info['start_time'] = str(show.start_time)
        data.append(show_info)

    return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    try:
        artist_id = request.form.get('artist_id')
        venue_id = request.form.get('venue_id')
        start_time = request.form.get('start_time')
        db.session.add(Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time))
        db.session.commit()
        # on successful db insert, flash success
        flash('Show was successfully listed!')
    except:
        # TODO: on unsuccessful db insert, flash an error instead.
        traceback.print_exc()
        flash('An error occurred. Show could not be listed.')

    return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
