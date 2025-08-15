cd gadget
mkdir gadget-bootstrap-dev
cp -r bootstrap/* gadget-bootstrap-dev
zip -r ../gadget-bootstrap.zip gadget-bootstrap-dev
mkdir gadget-server-dev
cp -r server/* gadget-server-dev
zip -r ../gadget-server.zip gadget-server-dev
rm -rf gadget-bootstrap-dev
rm -rf gadget-server-dev
