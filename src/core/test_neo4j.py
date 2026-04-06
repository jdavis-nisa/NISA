from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "neo4j://127.0.0.1:7687", 
    auth=("neo4j", "Keeva!@12K")
)
driver.verify_connectivity()
print("Neo4j connected successfully")
driver.close()