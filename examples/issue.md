# Bug: 登录接口在 token 过期时返回 500

## 背景

用户反馈：当 access token 过期后，请求 `/api/me` 偶尔返回 500，而不是预期的 401。

## 期望行为

- token 过期时返回 401
- 响应体包含稳定错误码：`TOKEN_EXPIRED`
- 增加单元测试覆盖该场景

## 线索

- 可能与 auth middleware 的异常处理有关
- 最近改动过 `decode_token` 的返回值
