DumpPath=/opt/env/noval-web/version/
DumpName=MongoBackup-$(date +%Y-%m-%d)
mongodump --host 127.0.0.1 -d members -o $DumpPath/$DumpName
cd $DumpPath
tar cjf ${DumpName}.tar.bz2 $DumpName
rm -rf $DumpPath/$DumpName
