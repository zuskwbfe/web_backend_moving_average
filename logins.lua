local logins = {}
for _, key in ipairs(redis.call('KEYS', 'session:*')) do
    table.insert(logins, redis.call('HGET', key, 'login'))
end
return logins
