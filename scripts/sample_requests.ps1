# Sample requests for BioShopping_AGENT

$chatPayload = @{ message = "Need 20 C57BL/6J mice and a draft email" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/chat" -Method Post -ContentType "application/json" -Body $chatPayload
