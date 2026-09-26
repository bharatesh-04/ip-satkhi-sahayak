from app.core.config import settings


class GraphService:
    def __init__(self):
        self.driver = None
        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
            )
        except Exception:
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    def expand(self, entities: list[str], jurisdictions: list[str]) -> list[dict]:
        if not self.driver or not entities:
            return []
        cypher = """
        MATCH (n)-[r]-(m)
        WHERE any(e IN $entities WHERE toLower(coalesce(n.name,'')) CONTAINS toLower(e))
          AND (coalesce(m.jurisdiction,'GLOBAL') IN $jurisdictions OR coalesce(m.jurisdiction,'GLOBAL')='GLOBAL')
        RETURN labels(n) AS n_labels, n.name AS n_name, type(r) AS rel,
               labels(m) AS m_labels, m.name AS m_name,
               coalesce(m.jurisdiction,'GLOBAL') AS m_jurisdiction
        LIMIT 50
        """
        try:
            with self.driver.session() as session:
                return [dict(x) for x in session.run(cypher, entities=entities, jurisdictions=jurisdictions)]
        except Exception:
            return []
