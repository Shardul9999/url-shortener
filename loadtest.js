import http from "k6/http";
import { check, sleep } from "k6";
import { Trend } from "k6/metrics";

// Custom metrics to surface p95/p99 explicitly in the summary
const redirectTrend = new Trend("redirect_duration", true);

export const options = {
  stages: [
    { duration: "10s", target: 5 }, // ramp from 0 → 100 VUs
    { duration: "20s", target: 5 }, // hold at 100 VUs
  ],
  thresholds: {
    // Test fails if p95 > 200 ms or p99 > 500 ms
    redirect_duration: ["p(95)<200", "p(99)<500"],
    http_req_failed: ["rate<0.01"], // < 1% error rate
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

// setup() runs once before any VU starts; return value is passed to every
// iteration of the default function as shared read-only data.
export function setup() {
  const res = http.post(
    `${BASE_URL}/shorten`,
    JSON.stringify({ original_url: "https://example.com" }),
    { headers: { "Content-Type": "application/json" } },
  );

  check(res, {
    "setup: POST /shorten → 201": (r) => r.status === 201,
  });

  if (res.status !== 201) {
    throw new Error(
      `setup failed: POST /shorten returned ${res.status} — ${res.body}`,
    );
  }

  const { short_code } = res.json();
  console.log(`setup: short_code = ${short_code}`);
  return { short_code };
}

// Default function — called once per VU per iteration for the duration of the test.
export default function (data) {
  const res = http.get(`${BASE_URL}/${data.short_code}`, {
    redirects: 0, // measure only the API response, not the final destination
  });

  check(res, {
    "GET /{code} → 302": (r) => r.status === 302,
    "Location header present": (r) => r.headers["Location"] !== undefined,
  });

  redirectTrend.add(res.timings.duration);

  sleep(0.1); // 100 ms think time — prevents thundering herd, models real traffic
}
