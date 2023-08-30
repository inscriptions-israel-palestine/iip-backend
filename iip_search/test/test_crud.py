import pytest

from iip_search import crud


class TestCrud:
    def test_list_locations(self, db_session, locations):
        for location in locations:
            db_session.add(location)

        locs = crud.list_locations(db_session)

        assert len(locs) == 4

    def test_get_inscription(self, db_session, inscriptions):
        for inscription in inscriptions:
            db_session.add(inscription)

        inscription = crud.get_inscription(db_session, "filename1")
