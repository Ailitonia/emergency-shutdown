# emergency-shutdown
适用于有UPS的家里云, 在停电时自动关机

建议将 HOST 配置为家里的网关, 一般来说就是光猫的 LAN 口 IP，这样几乎不会受到网络环境的影响导致误判

如需配置 systemd 服务, 可将 `emergency-shutdown-simple.service` 中第四行 `After=pve-guests.service` 删除, 这个是在 pve 宿主机环境上运行的启动顺序依赖, 其他环境可将其忽略
