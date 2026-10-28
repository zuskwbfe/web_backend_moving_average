local result = {}
for _, key in ipairs(redis.call('KEYS', 'session:*')) do
    local login = redis.call('HGET', key, 'login')
    table.insert(result, key .. ' -> ' .. login)
end
return result
