# SSH Tunnel Documentation

To access the internal UWM APIs, you need to establish an SSH tunnel using the provided PEM key.

## Connection Details

- **PEM Key Path:** `~/.ssh/valargen-staging_key.pem`
- **VM Public IP:** (Please provide the Azure VM Public IP)
- **VM Username:** azureuser (or as specified)
- **Internal API:** `uwm.internal.api:443`

## Quick Start Command

Run this in your terminal to create the tunnel:

```bash
ssh -i ~/.ssh/valargen-staging_key.pem -L 9000:uwm.internal.api:443 <username>@<VM_PUBLIC_IP>
```

## Testing the Connection

Once the tunnel is active, you can access the API locally at:
`https://localhost:9000`
