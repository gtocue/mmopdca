# infra/api_gateway.tf

resource "aws_api_gateway_rest_api" "public" {
  name = "mmopdca-public-api"
}

resource "aws_api_gateway_deployment" "public" {
  rest_api_id = aws_api_gateway_rest_api.public.id
  stage_name  = "prod"
}

# Free プラン用 API Key
resource "aws_api_gateway_api_key" "free" {
  name        = "free-tier-key"
  description = "Free tier: 10 requests/sec, 1000 calls/day"
  enabled     = true
}

# Free プラン UsagePlan
resource "aws_api_gateway_usage_plan" "free" {
  name        = "FreePlan"
  description = "Throttle and quota for free tier"
  api_stages {
    api_id = aws_api_gateway_rest_api.public.id
    stage  = aws_api_gateway_deployment.public.stage_name
  }

  throttle {
    rate_limit  = 10
    burst_limit = 20
  }

  quota {
    limit  = 1000
    period = "DAY"
  }
}

# UsagePlan に API Key を紐付け
resource "aws_api_gateway_usage_plan_key" "free_key" {
  key_id        = aws_api_gateway_api_key.free.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.free.id
}
