# Table grains and units

users: one account, signup/closure UTC, IANA timezone and declared primary provider.
subscriptions: half-open account/SKU effective intervals.
device_mappings: half-open installation/computer/account mappings; sharing is not proof of misuse.
businesses: local regional working schedules.
user_requests: one user action including blocked attempts, initiating route, task_family,
end-to-end duration, included/overage usage. Retries are not extra actions.
model_requests: one actual call, route, categories, price keys, outcome, raw performance.
usage: account/SKU/device/computer/model/provider/host/alias/price-key/six-hour UTC bucket totals.
model_catalog: model availability and illustrative Free eligibility.
routing: half-open alias-to-model intervals.
api_prices, copilot_aic_prices: separate dated USD-per-million text-token snapshots and input tiers.
hosting_rates: fictional API-cost multipliers, Azure .60 and others .70.
sku_budgets: monthly allowances except lifetime trial; illustrative Free and Student policies.

total_input_tokens = uncached_tokens + cache_read_tokens.
ordinary_uncached_tokens is the legacy uncached alias; cache_write_tokens is a subset.
ordinary_billed_input_tokens = uncached_tokens - cache_write_tokens.
Writes are total rates, not surcharges; unsupported writes are zero.
API dollars, AIC and hosting dollars are distinct. AIC USD proxy = AIC * .01, not revenue.
Included allowance is not revenue. Pro overage is limited per account/month.
Action counts use the initiating time/route; call counts use actual time/route and price keys.
Use ratios of sums and raw-call percentiles. Missing performance is null, not zero.
Window: 2026-09-01 inclusive through 2026-12-01 exclusive, UTC.
Free uses the cheapest eligible available OpenAI API route for 10k input (90% read), 1k output, no writes.
Model launch dates, quality, latency and all behavior are fictional, not historical claims.
The warm-cache model is a simplification, not a provider cache emulator.
