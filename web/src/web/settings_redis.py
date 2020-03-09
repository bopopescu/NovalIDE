# coding:utf-8
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'session'
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'
SESSION_COOKIE_AGE = 86400 * 10

DEFAULT_REDIS_CACHE = "default"
SESSION_REDIS_CACHE = "session"
MEMBERS_REDIS_CACHE = "members"

CACHES = {
    DEFAULT_REDIS_CACHE: {
        "BACKEND": "redis_cache.cache.RedisCache",
        "LOCATION": "127.0.0.1:6379:0",
        "TIMEOUT": 300,
        "KEY_PREFIX": "default",
        "VERSION": 1,
        "OPTIONS": {
            'SOCKET_TIMEOUT': 5
        }
    },
    SESSION_REDIS_CACHE: {
        "BACKEND": "redis_cache.cache.RedisCache",
        "LOCATION": "127.0.0.1:6379:1",
        "TIMEOUT": SESSION_COOKIE_AGE,
        "KEY_PREFIX": "session",
        "VERSION": 1,
        "OPTIONS": {
            'SOCKET_TIMEOUT': 5
        }
    },
    MEMBERS_REDIS_CACHE: {
        "BACKEND": "redis_cache.cache.RedisCache",
        "LOCATION": "127.0.0.1:6379:2",
        "OPTIONS": {
            'SOCKET_TIMEOUT': 5
        }
    },
}
