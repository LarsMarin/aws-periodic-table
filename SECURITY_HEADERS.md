# Security Headers Configuration

## Overview

This document describes the security headers that should be configured at the server/CDN level for optimal security.

## Required HTTP Headers

The following headers **cannot** be set via HTML `<meta>` tags and must be configured at the server or CDN level:

### 1. X-Frame-Options
```
X-Frame-Options: DENY
```
**Purpose:** Prevents clickjacking attacks by disallowing the page to be embedded in iframes.

### 2. Content-Security-Policy (frame-ancestors)
```
Content-Security-Policy: frame-ancestors 'none'
```
**Purpose:** Modern alternative to X-Frame-Options, provides more granular control.

### 3. Strict-Transport-Security (HSTS)
```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```
**Purpose:** Forces HTTPS connections and prevents protocol downgrade attacks.

### 4. Permissions-Policy
```
Permissions-Policy: geolocation=(), microphone=(), camera=(), payment=(), usb=()
```
**Purpose:** Disables unnecessary browser features to reduce attack surface.

## CloudFront Configuration

For AWS CloudFront distributions, add these headers using a Response Headers Policy:

### Option 1: AWS Console

1. Go to CloudFront → Policies → Response headers
2. Create a new policy with the following settings:

**Security Headers:**
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
- Referrer-Policy: strict-origin-when-cross-origin

**Custom Headers:**
```
Permissions-Policy: geolocation=(), microphone=(), camera=(), payment=(), usb=()
```

### Option 2: CloudFormation Template

Add to your CloudFront distribution configuration:

```yaml
ResponseHeadersPolicyId: !Ref SecurityHeadersPolicy

SecurityHeadersPolicy:
  Type: AWS::CloudFront::ResponseHeadersPolicy
  Properties:
    ResponseHeadersPolicyConfig:
      Name: SecurityHeaders
      SecurityHeadersConfig:
        StrictTransportSecurity:
          AccessControlMaxAgeSec: 31536000
          IncludeSubdomains: true
          Preload: true
          Override: true
        ContentTypeOptions:
          Override: true
        FrameOptions:
          FrameOption: DENY
          Override: true
        ReferrerPolicy:
          ReferrerPolicy: strict-origin-when-cross-origin
          Override: true
        XSSProtection:
          ModeBlock: true
          Protection: true
          Override: true
      CustomHeadersConfig:
        Items:
          - Header: Permissions-Policy
            Value: "geolocation=(), microphone=(), camera=(), payment=(), usb=()"
            Override: true
```

### Option 3: Lambda@Edge

For more complex header manipulation, use Lambda@Edge:

```javascript
exports.handler = async (event) => {
    const response = event.Records[0].cf.response;
    const headers = response.headers;

    headers['x-frame-options'] = [{ key: 'X-Frame-Options', value: 'DENY' }];
    headers['x-content-type-options'] = [{ key: 'X-Content-Type-Options', value: 'nosniff' }];
    headers['strict-transport-security'] = [{ 
        key: 'Strict-Transport-Security', 
        value: 'max-age=31536000; includeSubDomains; preload' 
    }];
    headers['referrer-policy'] = [{ 
        key: 'Referrer-Policy', 
        value: 'strict-origin-when-cross-origin' 
    }];
    headers['permissions-policy'] = [{ 
        key: 'Permissions-Policy', 
        value: 'geolocation=(), microphone=(), camera=(), payment=(), usb=()' 
    }];

    return response;
};
```

## S3 Static Website Hosting

If using S3 static website hosting directly (not recommended for production), headers must be set via:

1. **CloudFront** (recommended) - Use Response Headers Policy as shown above
2. **API Gateway + Lambda** - Add headers in Lambda response
3. **Application Load Balancer** - Configure response headers in ALB rules

## Verification

Test your security headers using:

1. **Security Headers Scanner:** https://securityheaders.com/
2. **Mozilla Observatory:** https://observatory.mozilla.org/
3. **Chrome DevTools:** Network tab → Response Headers

## Current Implementation Status

✅ **Implemented via Meta Tags:**
- Content-Security-Policy (partial)
- X-Content-Type-Options
- Referrer-Policy

⚠️ **Requires Server Configuration:**
- X-Frame-Options
- Strict-Transport-Security (HSTS)
- Permissions-Policy
- Content-Security-Policy: frame-ancestors

## Recommended Security Score Targets

- **Security Headers:** A+ rating
- **Mozilla Observatory:** A+ rating
- **SSL Labs:** A+ rating

## Additional Resources

- [OWASP Secure Headers Project](https://owasp.org/www-project-secure-headers/)
- [MDN Web Security](https://developer.mozilla.org/en-US/docs/Web/Security)
- [AWS CloudFront Security Best Practices](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/security-best-practices.html)
