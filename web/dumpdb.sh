DumpPath=/opt/web/version/

DumpName=MongoBackup-members-$(date +%Y-%m-%d)
mongodump --host 127.0.0.1 -d members -o $DumpPath/$DumpName
cd $DumpPath
tar cjf ${DumpName}.tar.bz2 $DumpName
rm -rf $DumpPath/$DumpName

DumpName=MongoBackup-pypi-$(date +%Y-%m-%d)
mongodump --host 127.0.0.1 -d pypi -o $DumpPath/$DumpName
tar cjf ${DumpName}.tar.bz2 $DumpName
rm -rf $DumpPath/$DumpName
