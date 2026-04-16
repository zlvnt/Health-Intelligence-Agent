"""Seed Qdrant with basic nutrition data. Run once before starting the bot."""

from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_qdrant import QdrantVectorStore

NUTRITION_DATA = [
    "White rice (1 cup, cooked): 206 kcal, 4.3g protein, 44.5g carbs, 0.4g fat",
    "Fried rice / nasi goreng (1 plate): 370 kcal, 10g protein, 50g carbs, 14g fat",
    "Chicken breast (grilled, 100g): 165 kcal, 31g protein, 0g carbs, 3.6g fat",
    "Chicken thigh (grilled, 100g): 209 kcal, 26g protein, 0g carbs, 10.9g fat",
    "Egg (1 large, boiled): 78 kcal, 6.3g protein, 0.6g carbs, 5.3g fat",
    "Egg (1 large, fried): 92 kcal, 6.3g protein, 0.4g carbs, 7g fat",
    "Banana (1 medium): 105 kcal, 1.3g protein, 27g carbs, 0.4g fat",
    "Apple (1 medium): 95 kcal, 0.5g protein, 25g carbs, 0.3g fat",
    "Bread (1 slice, white): 79 kcal, 2.7g protein, 15g carbs, 1g fat",
    "Bread (1 slice, whole wheat): 81 kcal, 3.6g protein, 13.8g carbs, 1.1g fat",
    "Oatmeal (1 cup, cooked): 154 kcal, 5.3g protein, 27.4g carbs, 2.6g fat",
    "Pasta (1 cup, cooked): 220 kcal, 8.1g protein, 43.2g carbs, 1.3g fat",
    "Salmon (100g, baked): 208 kcal, 20g protein, 0g carbs, 13g fat",
    "Tuna (100g, canned): 116 kcal, 25.5g protein, 0g carbs, 0.8g fat",
    "Beef steak (100g, grilled): 271 kcal, 26g protein, 0g carbs, 18g fat",
    "Tofu (100g, firm): 76 kcal, 8g protein, 1.9g carbs, 4.8g fat",
    "Tempeh (100g): 192 kcal, 20g protein, 7.6g carbs, 11g fat",
    "Milk (1 cup, whole): 149 kcal, 8g protein, 12g carbs, 8g fat",
    "Greek yogurt (1 cup, plain): 100 kcal, 17g protein, 6g carbs, 0.7g fat",
    "Avocado (1 medium): 240 kcal, 3g protein, 12.8g carbs, 22g fat",
    "Sweet potato (1 medium, baked): 103 kcal, 2.3g protein, 24g carbs, 0.1g fat",
    "Potato (1 medium, baked): 161 kcal, 4.3g protein, 37g carbs, 0.2g fat",
    "Broccoli (1 cup, cooked): 55 kcal, 3.7g protein, 11.2g carbs, 0.6g fat",
    "Spinach (1 cup, cooked): 41 kcal, 5.3g protein, 6.8g carbs, 0.5g fat",
    "Almonds (28g / 1oz): 164 kcal, 6g protein, 6g carbs, 14g fat",
    "Peanut butter (2 tbsp): 188 kcal, 8g protein, 6g carbs, 16g fat",
    "Orange juice (1 cup): 112 kcal, 1.7g protein, 26g carbs, 0.5g fat",
    "Coffee (black, 1 cup): 2 kcal, 0.3g protein, 0g carbs, 0g fat",
    "Coca-Cola (330ml can): 139 kcal, 0g protein, 39g carbs, 0g fat",
    "Pizza (1 slice, cheese): 272 kcal, 12g protein, 34g carbs, 10g fat",
    "Burger (beef, standard): 354 kcal, 20g protein, 29g carbs, 17g fat",
    "French fries (medium serving): 365 kcal, 4g protein, 44g carbs, 17g fat",
    "Salad (mixed greens, no dressing, 1 bowl): 20 kcal, 1.5g protein, 3.5g carbs, 0.2g fat",
    "Protein shake (1 scoop whey + water): 120 kcal, 24g protein, 3g carbs, 1.5g fat",
    "Rendang (100g): 193 kcal, 22g protein, 3g carbs, 11g fat",
    "Noodle soup / mie kuah (1 bowl): 350 kcal, 12g protein, 45g carbs, 12g fat",
    "Instant noodle / Indomie (1 pack): 380 kcal, 8g protein, 52g carbs, 15g fat",
    "Sate ayam (10 sticks): 470 kcal, 36g protein, 8g carbs, 32g fat",
    "Gado-gado (1 plate): 280 kcal, 12g protein, 20g carbs, 18g fat",
    "Nasi uduk (1 plate): 350 kcal, 6g protein, 48g carbs, 14g fat",
]


def seed():
    embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    QdrantVectorStore.from_texts(
        texts=NUTRITION_DATA,
        embedding=embeddings,
        url="http://localhost:6333",
        collection_name="nutrition_db",
        force_recreate=True,
    )
    print(f"Seeded {len(NUTRITION_DATA)} nutrition entries to Qdrant.")


if __name__ == "__main__":
    seed()
