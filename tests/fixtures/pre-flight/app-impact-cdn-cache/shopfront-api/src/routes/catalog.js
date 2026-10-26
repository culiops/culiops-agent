const express = require("express");
const { getSession } = require("../session");
const { listProducts, getCart, addCartItem } = require("../store");

const router = express.Router();

// Product list. Members see their member price.
router.get("/api/catalog/products", async (req, res) => {
  const session = await getSession(req.cookies.sid);
  const products = await listProducts();
  res.json(
    products.map((p) => ({
      id: p.id,
      name: p.name,
      price: session && session.isMember ? p.memberPrice : p.listPrice,
    }))
  );
});

// The signed-in user's cart, with recommendations from their order history.
router.get("/api/catalog/cart", async (req, res) => {
  const session = await getSession(req.cookies.sid);
  if (!session) return res.status(401).json({ error: "sign in" });
  res.json(await getCart(session.userId));
});

router.post("/api/catalog/cart/items", async (req, res) => {
  const session = await getSession(req.cookies.sid);
  if (!session) return res.status(401).json({ error: "sign in" });
  await addCartItem(session.userId, req.body);
  res.status(201).end();
});

module.exports = router;
