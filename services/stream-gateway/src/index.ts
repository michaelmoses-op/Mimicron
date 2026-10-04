import { createApp } from "./app.js";
import { startKafkaConsumer } from "./consumer.js";
import { authMiddleware } from "./auth.js";
import { handleStream } from "./sse.js";

const port = Number(process.env.PORT ?? "8082");
const app = createApp();

app.get("/v1/stream", authMiddleware, handleStream);

startKafkaConsumer().catch((err) => {
  console.error("kafka consumer failed", err);
});

app.listen(port, () => {
  console.log(JSON.stringify({ msg: "stream-gateway listening", port }));
});
