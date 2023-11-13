import json
import logging
import os

import redis
import redis.commands.json.path as redis_path
import redis.commands.search.aggregation as aggregation
import redis.commands.search.field as redis_field
import redis.commands.search.reducers as reducers


import redis.exceptions

from redis.commands.search.indexDefinition import IndexDefinition, IndexType

logger = logging.getLogger(__name__)

COUNTABLE_FACETS = [
    "genres",
    "physical_types",
    "languages",
    "religions",
    "materials",
    "city",
]


class RedisConnection:
    def __init__(self):
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.username = os.getenv("REDIS_USER", "")
        self.password = os.getenv("REDIS_PASSWORD", "")
        self.search_schema = (
            redis_field.TextField("$.description", as_name="description"),
            redis_field.NumericField("$.not_after", as_name="not_after"),
            redis_field.NumericField("$.not_before", as_name="not_before"),
            redis_field.TextField("$.title", as_name="title"),
            redis_field.TagField(
                "$.bibliographic_entries.*", as_name="bibliographic_entries"
            ),
            redis_field.TextField("$.city", as_name="city"),
            redis_field.TagField("$.figures.*", as_name="figures"),
            redis_field.TagField("$.genres.*", as_name="genres"),
            redis_field.TagField("$.physical_types.*", as_name="physical_types"),
            redis_field.TagField("$.languages.*", as_name="languages"),
            redis_field.TagField("$.religions.*", as_name="religions"),
            redis_field.TagField("$.materials.*", as_name="materials"),
        )
        self.r = redis.Redis(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            decode_responses=True,
        )

    def add_document(self, doc):
        self.r.json().set(
            f"iip:{doc['id']}",
            redis_path.Path.root_path(),
            doc,
        )

    def close(self):
        self.r.close()

    def count_facets(self, q):
        reqs = [
            aggregation.AggregateRequest(q).group_by(
                [f"@{i}"], reducers.count().alias("total")
            )
            for i in COUNTABLE_FACETS
        ]
        results = [(row[0], row[1], int(row[3])) for req in reqs for row in self.r.ft().aggregate(req).rows]  # type: ignore
        d = {}
        for facet, name, count in results:
            if facet == "city":
                d.setdefault("cities", []).append((name, count))
            else:
                d.setdefault(facet, []).append((name, count))

        return d

    def create_index(self):
        try:
            self.r.ft().create_index(
                self.search_schema,
                definition=IndexDefinition(index_type=IndexType.JSON),
            )
        except redis.exceptions.ResponseError as _e:
            logger.warn("Index already created.")

    def search(self, q):
        return self.r.ft().search(q)
