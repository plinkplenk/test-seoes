crontab -e
0 0 1 * * curl -X 'PUT' 'http://localhost:8000/admin/reset_query_limits/' -H 'accept: application/json' -H 'Cookie: bonds=c87d095c0d020fba6d5671484664c1825b9fe9c69ef59f324f95b96a2fa7ae0b'