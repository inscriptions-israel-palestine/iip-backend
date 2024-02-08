import logging

from iip_search import crud


logger = logging.getLogger(__name__)


class TestCrud:
    def test_list_inscriptions_by_description_place_id(self, db_session, inscriptions):
        for inscription in inscriptions:
            db_session.add(inscription)

        q = crud.list_inscriptions_query(db_session, None, "filename2")

        assert len(q.all()) == 1

    def test_list_locations(self, db_session, locations):
        for location in locations:
            db_session.add(location)

        locs = crud.list_locations(db_session)

        assert len(locs) == 4

    def test_get_inscription(self, db_session, inscriptions):
        for inscription in inscriptions:
            db_session.add(inscription)

        inscription = crud.get_inscription(db_session, "filename1")

    def test_facet_cities_query(self, db_session, cities, inscriptions):
        for city in cities:
            db_session.add(city)

        for inscription in inscriptions:
            db_session.add(inscription)

        city_facets = crud.facet_cities_query(db_session).all()

        assert len(city_facets) == 2
        assert city_facets[0][1] == 1
        assert city_facets[1][1] == 1
