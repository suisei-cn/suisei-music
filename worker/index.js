import { AwsClient } from "aws4fetch";

const aws = new AwsClient({
  accessKeyId: AWS_ACCESS_KEY_ID,
  secretAccessKey: AWS_SECRET_ACCESS_KEY,
  region: AWS_DEFAULT_REGION,
  service: "s3"
});

async function handleRequest(request) {
  if (request.method != "GET") {
    return new Response("Method Not Allowed", { status: 405 });
  }

  let path = new URL(request.url).pathname;
  let query = "?response-cache-control=public, max-age=31536000";

  if (path.endsWith(".ogg")) {
    query += "&response-content-type=audio/ogg";
  }

  if (path.endsWith(".m4a")) {
    query += "&response-content-type=audio/mp4";
  }

  let url = AWS_S3_ENDPOINT + path + query;
  let headers = request.headers;

  return await aws.fetch(url, {
    method: "GET",
    headers: headers.has("range") ? { range: headers.get("range") } : {},
    cf: { cacheEverything: true }
  });
}

addEventListener("fetch", function(event) {
  event.respondWith(handleRequest(event.request));
});
