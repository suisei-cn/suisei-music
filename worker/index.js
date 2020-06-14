import { AwsClient } from "aws4fetch";

const aws = new AwsClient({
  accessKeyId: AWS_ACCESS_KEY_ID,
  secretAccessKey: AWS_SECRET_ACCESS_KEY,
  region: AWS_DEFAULT_REGION,
  service: "s3"
});

function configParams(path) {
  switch (path.split(".").pop()) {
    case "json":
      return {
        "response-cache-control": "no-cache",
        "response-content-type": "application/json;charset=utf-8"
      };
    case "m4a":
      return {
        "response-cache-control": "public,max-age=31536000,immutable",
        "response-content-type": "audio/mp4"
      };
    default:
      return {};
  }
}

async function handleRequest(request) {
  if (request.method != "GET") {
    return new Response("Method Not Allowed", { status: 405 });
  }

  const path = new URL(request.url).pathname.substring(1) || "meta.json";
  const query = new URLSearchParams(configParams(path)).toString();
  const url = `${AWS_S3_ENDPOINT}/${path}?${query}`;

  const range = request.headers.get("range");
  const headers = range ? { range: range } : {};

  return await aws.fetch(url, {
    method: "GET",
    headers: headers,
    cf: { cacheEverything: true }
  });
}

addEventListener("fetch", function(event) {
  event.respondWith(handleRequest(event.request));
});
