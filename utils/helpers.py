
import redis
from flask_jwt_extended import JWTManager

blacklist = redis.StrictRedis(host='redis', port=6379, db=0, decode_responses=True)

def init_jwt_manager(app):
    jwt = JWTManager(app)


    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload['jti']
        token_in_redis = blacklist.get(jti)
        return token_in_redis is not None

    return jwt
