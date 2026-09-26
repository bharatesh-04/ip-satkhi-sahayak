CREATE CONSTRAINT product_name IF NOT EXISTS FOR (n:Product) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT source_id IF NOT EXISTS FOR (n:SourceDocument) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT provision_id IF NOT EXISTS FOR (n:Provision) REQUIRE n.id IS UNIQUE;

// Core relationship vocabulary
// (Product)-[:CONTAINS]->(Ingredient)
// (Ingredient)-[:IS_BIOLOGICAL_RESOURCE]->(BiologicalResource)
// (Product)-[:MAY_INVOLVE]->(TraditionalKnowledge)
// (Product)-[:CLASSIFIED_AS]->(RegulatoryCategory)
// (Product)-[:SEEKING]->(IPType)
// (Requirement)-[:GOVERNED_BY]->(Provision)
// (Provision)-[:PART_OF]->(LegalInstrument)
// (Provision)-[:APPLIES_IN]->(Jurisdiction)
// (Provision)-[:SUPERSEDES]->(Provision)
// (Evidence)-[:SUPPORTS]->(Claim)
// (SourceDocument)-[:HAS_VERSION]->(Version)
