# ===== Port 12345 =====
New-NetFirewallRule -DisplayName "Port 12345 Eingehend TCP" -Direction Inbound -LocalPort 12345 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Port 12345 Ausgehend TCP" -Direction Outbound -LocalPort 12345 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Port 12345 Eingehend UDP" -Direction Inbound -LocalPort 12345 -Protocol UDP -Action Allow
New-NetFirewallRule -DisplayName "Port 12345 Ausgehend UDP" -Direction Outbound -LocalPort 12345 -Protocol UDP -Action Allow

# ===== Port 9001 =====
New-NetFirewallRule -DisplayName "Port 9001 Eingehend TCP" -Direction Inbound -LocalPort 9001 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Port 9001 Ausgehend TCP" -Direction Outbound -LocalPort 9001 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Port 9001 Eingehend UDP" -Direction Inbound -LocalPort 9001 -Protocol UDP -Action Allow
New-NetFirewallRule -DisplayName "Port 9001 Ausgehend UDP" -Direction Outbound -LocalPort 9001 -Protocol UDP -Action Allow

# ===== Port 1883 =====
New-NetFirewallRule -DisplayName "Port 1883 Eingehend TCP" -Direction Inbound -LocalPort 1883 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Port 1883 Ausgehend TCP" -Direction Outbound -LocalPort 1883 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Port 1883 Eingehend UDP" -Direction Inbound -LocalPort 1883 -Protocol UDP -Action Allow
New-NetFirewallRule -DisplayName "Port 1883 Ausgehend UDP" -Direction Outbound -LocalPort 1883 -Protocol UDP -Action Allow
