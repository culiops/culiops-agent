const express = require("express");
const cookieParser = require("cookie-parser");

const app = express();
app.use(cookieParser());
app.use(express.json());
app.use(require("./routes/catalog"));
app.get("/healthz", (_req, res) => res.sendStatus(200));

app.listen(process.env.PORT || 3000);
