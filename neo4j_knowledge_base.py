from collections import defaultdict
from typing import Any, Dict, List, Text

from neo4j import GraphDatabase
from rasa_sdk.knowledge_base.storage import KnowledgeBase


def _dict_to_cypher(data):
    pieces = []
    for k, v in data.items():
        piece = "{}: '{}'".format(k, v)
        pieces.append(piece)

    join_piece = ", ".join(pieces)

    return "{" + join_piece + "}"


class Neo4jKnowledgeBase(KnowledgeBase):
    def __init__(self, uri, user, password):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

        self.representation_attribute = defaultdict(lambda: "name")

        self.relation_attributes = {
            "Disease": {"alternative": "别称", "regularity": "发生规律", "introduction": "简介", "image": "图例", "alternative": "别称", "feature": "形态特征", "treatment": "防治方法", "lifestyle": "生活习性", "symptom": "症状", "crop": "危害作物", "Abstract": "摘要", "introduction": "简介", "url": "网址", "keyword": "关键字", "title": "研究文献", "periodical": "期刊", "author": "作者"},
            "Insect": {"alternative": "别称", "regularity": "发生规律", "introduction": "简介", "image": "图例", "alternative": "别称", "feature": "形态特征", "treatment": "防治方法", "lifestyle": "生活习性", "symptom": "症状", "crop": "危害作物", "Abstract": "摘要", "introduction": "简介", "url": "网址", "keyword": "关键字", "title": "研究文献", "periodical": "期刊", "author": "作者"},
            "Image": {},
            "Abstract": {},
            "Introduction": {},
            "Regularity": {},
            "ScientificName": {},
            "Treatment": {},
            "Symptom": {},
            "Crop": {"disease": "虫害", "insect": "虫害"},
            "Title": {"abstract": "摘要", "keyword": "关键字", "url": "网址", "periodical": "期刊", "author": "作者"},
            "Alternative": {},
            "Feature": {},
            "Periodical": {},
            "Author": {},
            "Keyword": {}
        }

        super().__init__()

    def close(self):
        self._driver.close()

    async def get_attributes_of_object(self, object_type: Text) -> List[Text]:
        # transformer for query
        object_type = object_type.capitalize()

        result = self.do_get_attributes_of_object(object_type)

        return result

    def do_get_attributes_of_object(self, object_type) -> List[Text]:
        with self._driver.session() as session:
            result = session.write_transaction(
                self._do_get_attributes_of_object, object_type
            )

        result = result + list(self.relation_attributes[object_type].keys())

        return result

    def _do_get_attributes_of_object(self, tx, object_type) -> List[Text]:
        query = "MATCH (o:{object_type}) RETURN o LIMIT 1".format(
            object_type=object_type
        )
        print(query)
        result = tx.run(
            query,
        )

        record = result.single()

        if record:
            return list(record[0].keys())

        return []

    async def get_representation_attribute_of_object(self, object_type: Text) -> Text:
        """
        Returns a lamdba function that takes the object and returns a string
        representation of it.
        Args:
            object_type: the object type
        Returns: lamdba function
        """
        return self.representation_attribute[object_type]

    def do_get_objects(
        self,
        object_type: Text,
        attributions: Dict[Text, Text],
        relations: Dict[Text, Text],
        limit: int,
    ):
        with self._driver.session() as session:
            result = session.write_transaction(
                self._do_get_objects, object_type, attributions, relations, limit
            )

        return result

    def do_get_object(
        self,
        object_type: Text,
        object_identifier: Text,
        key_attribute: Text,
        representation_attribute: Text,
    ):
        with self._driver.session() as session:
            result = session.write_transaction(
                self._do_get_object,
                object_type,
                object_identifier,
                key_attribute,
                representation_attribute,
                self.relation_attributes[object_type],
            )

        return result

    @staticmethod
    def _do_get_objects(
        tx,
        object_type: Text,
        attributions: Dict[Text, Text],
        relations: Dict[Text, Text],
        limit: int,
    ):
        print("<_do_get_objects>: ", object_type, attributions, relations, limit)
        if not relations:
            # attr only, simple case
            query = "MATCH (o:{object_type} {attrs}) RETURN o LIMIT {limit}".format(
                object_type=object_type,
                attrs=_dict_to_cypher(attributions),
                limit=limit,
            )
            print(query)
            result = tx.run(
                query,
            )

            return [dict(record["o"].items()) for record in result]
        else:
            basic_query = "MATCH (o:{object_type} {attrs})".format(
                object_type=object_type,
                attrs=_dict_to_cypher(attributions),
            )
            sub_queries = []
            for k, v in relations.items():
                sub_query = "MATCH (o)-[:{}]->({{name: '{}'}})".format(k, v)

            where_clause = "WHERE EXISTS { " + sub_query + " }"
            for sub_query in sub_queries[1:]:
                where_clause = "WHERE EXISTS { " + sub_query + " " + where_clause + " }"

            query = (
                basic_query + " " + where_clause + " RETURN o LIMIT {}".format(limit)
            )

            print(query)
            result = tx.run(
                query,
            )

            return [dict(record["o"].items()) for record in result]

    @staticmethod
    def _do_get_object(
        tx,
        object_type: Text,
        object_identifier: Text,
        key_attribute: Text,
        representation_attribute: Text,
        relation: Dict[Text, Text],
    ):
        print(
            "<_do_get_object>: ",
            object_type,
            object_identifier,
            key_attribute,
            representation_attribute,
            relation,
        )
        # preprocess attr value
        if object_identifier.isdigit():
            object_identifier = int(object_identifier)
        else:
            object_identifier = '"{}"'.format(object_identifier)

        # try match key first
        query = "MATCH (o:{object_type} {{{key}:{value}}}) RETURN o, ID(o)".format(
            object_type=object_type, key=key_attribute, value=object_identifier
        )
        print(query)
        result = tx.run(
            query,
        )
        record = result.single()

        if record:
            attr_dict = dict(record[0].items())
            oid = record[1]
        else:
            # try to match representation attribute
            query = "MATCH (o:{object_type} {{{key}:{value}}}) RETURN o, ID(o)".format(
                object_type=object_type,
                key=representation_attribute,
                value=object_identifier,
            )
            print(query)
            result = tx.run(
                query,
            )
            record = result.single()
            if record:
                attr_dict = dict(record[0].items())
                oid = record[1]
            else:
                # finally, failed
                attr_dict = None

        if attr_dict is None:
            return None

        relation_attr = {}
        for k, v in relation.items():
            query = "MATCH (o)-[:{}]->(t) WHERE ID(o)={} RETURN t.name".format(v, oid)
            print(query)
            result = tx.run(query)
            record = result.single()
            if record:
                attr = record[0]
            else:
                attr = None

            relation_attr[k] = attr

        return {**attr_dict, **relation_attr}

    async def get_objects(
        self, object_type: Text, attributes: List[Dict[Text, Text]], limit: int = 1000
    ) -> List[Dict[Text, Any]]:
        """
        Query the knowledge base for objects of the given type. Restrict the objects
        by the provided attributes, if any attributes are given.
        Args:
            object_type: the object type
            attributes: list of attributes
            limit: maximum number of objects to return
        Returns: list of objects
        """
        print("get_objects", object_type, attributes, limit)

        # convert attributes to dict
        attrs = {}
        for a in attributes:
            attrs[a["name"]] = a["value"]

        # transformer for query
        object_type = object_type.capitalize()

        # split into attrs and relations
        attrs_filter = {}
        relations_filter = {}
        relation = self.relation_attributes[object_type]
        for k, v in attrs.items():
            if k in relation:
                relations_filter[relation[k]] = v
            else:
                attrs_filter[k] = v

        result = self.do_get_objects(object_type, attrs_filter, relations_filter, limit)

        return result

    async def get_object(
        self, object_type: Text, object_identifier: Text
    ) -> Dict[Text, Any]:
        """
        Returns the object of the given type that matches the given object identifier.
        Args:
            object_type: the object type
            object_identifier: value of the key attribute or the string
            representation of the object
        Returns: the object of interest
        """
        # transformer for query
        object_type = object_type.capitalize()

        result = self.do_get_object(
            object_type,
            object_identifier,
            await self.get_key_attribute_of_object(object_type),
            await self.get_representation_attribute_of_object(object_type),
        )

        return result


if __name__ == "__main__":
    import asyncio

    # 此处输入自己的用户名和密码
    kb = Neo4jKnowledgeBase("bolt://localhost:7687", "neo4j", "wxkno.12002922")
    loop = asyncio.get_event_loop()

    result = loop.run_until_complete(kb.get_objects("disease", [], 5))
    print(result)

    result = loop.run_until_complete(
        kb.get_objects("insect", [{"name": "insect", "value": "玉米蚜"}], 5)
    )
    print(result)

    result = loop.run_until_complete(
        kb.get_objects(
            "treatment",
            [{"name": "insect", "value": "玉米蚜"}, {"name": "treatment", "value": "防治方法"}],
            5,
        )
    )
    print(result)

    result = loop.run_until_complete(kb.get_object("insect", "玉米蚜"))
    print(result)

    loop.close()
