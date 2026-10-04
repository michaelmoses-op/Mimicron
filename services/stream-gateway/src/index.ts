import { createApp } from "./app.js";

const port = Number(process.env.PORT ?? "8082");
createApp().listen(port, () => {
  console.log(JSON.stringify({ msg: "stream-gateway listening", port }));
});
