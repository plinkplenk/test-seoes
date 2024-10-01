$headers = @{
    "Cookie" = "bonds=c87d095c0d020fba6d5671484664c1825b9fe9c69ef59f324f95b96a2fa7ae0b"
}
Invoke-WebRequest -Uri "http://localhost:8000/admin/reset_query_limits/" -Method PUT -Headers $headers -ContentType "application/json"