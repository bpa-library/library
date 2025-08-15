import os

# Configure from environment variables
# B2_KEY_ID = os.getenv('0050a69e0f956a00000000002')  # Set these in your OS or Netlify
# B2_APP_KEY = os.getenv('K005KxHLolOknutv3f7yyEyg8JUK8Tg')
# B2_BUCKET = "audiobooks-free"

#backblaze.com
B2_KEY_ID = '0050a69e0f956a00000000002'  # Set these in your OS or Netlify
B2_APP_KEY = 'K005KxHLolOknutv3f7yyEyg8JUK8Tg'
B2_BUCKET = "audiobooks-free"
B2_ENDPOINT = "https://s3.us-east-005.backblazeb2.com"  

#postgresql
postgresql_DATABASE_URL = 'postgresql://neondb_owner:npg_W2pRMBiSrHe9@ep-long-morning-a1zn9pkz-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'

# Host: ep-long-morning-a1zn9pkz-pooler.ap-southeast-1.aws.neon.tech   =   ep-cool-darkness-123456.us-east-2.aws.neon.tech
# Database: neondb
# User: neondb_owner         = your-username 
# Password: npg_W2pRMBiSrHe9 = auto-generated (copy this)

# postgresql://alex:AbC123dEf@ep-cool-darkness-a1b2c3d4-pooler.us-east-2.aws.neon.tech/dbname?sslmode=require&channel_binding=require
#              ^    ^         ^                         ^                              ^
#        role -|    |         |- hostname               |- pooler option               |- database
#                   |
#                   |- password