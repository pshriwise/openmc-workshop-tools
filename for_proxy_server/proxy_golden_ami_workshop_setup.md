# Starting a New Workshop Using the Golden Proxy AMI

These instructions describe how to launch a **new workshop proxy
server** using a previously created **Golden AMI** that already contains
the Nitro Enclave + nginx configuration.

This dramatically simplifies workshop setup.

The Golden AMI already contains:

-   nginx configured for PKCS11 TLS
-   aws-nitro-enclaves-acm
-   aws-nitro-enclaves-cli
-   enclave allocator configuration
-   nginx proxy templates
-   required system services enabled

Because these fragile steps are already baked into the image, launching
a new workshop proxy takes only a few minutes.
