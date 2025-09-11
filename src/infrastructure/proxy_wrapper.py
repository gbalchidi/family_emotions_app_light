"""
Simple HTTP proxy wrapper for Anthropic API that routes through SOCKS5
"""
import os
import logging
from typing import Optional
import httpx
from httpx_socks import SyncProxyTransport
import asyncio
from aiohttp import web
import aiohttp
import aiohttp_socks

logger = logging.getLogger(__name__)


class ProxyServer:
    def __init__(self, socks_proxy: str = "socks5://127.0.0.1:1080", port: int = 8888):
        self.socks_proxy = socks_proxy
        self.port = port
        self.app = web.Application()
        self.setup_routes()
    
    def setup_routes(self):
        self.app.router.add_route('*', '/{path:.*}', self.handle_request)
    
    async def handle_request(self, request):
        """Forward requests through SOCKS5 proxy"""
        try:
            # Get the target URL
            target_url = str(request.url).replace(f'http://localhost:{self.port}', 'https://api.anthropic.com')
            
            # Create connector with SOCKS5 proxy
            connector = aiohttp_socks.ProxyConnector.from_url(self.socks_proxy)
            
            # Forward the request
            async with aiohttp.ClientSession(connector=connector) as session:
                # Copy headers
                headers = dict(request.headers)
                headers.pop('Host', None)
                
                # Read body
                body = await request.read()
                
                # Make request through proxy
                async with session.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    data=body,
                    ssl=False
                ) as response:
                    # Get response body
                    response_body = await response.read()
                    
                    # Return response
                    return web.Response(
                        body=response_body,
                        status=response.status,
                        headers=response.headers
                    )
        except Exception as e:
            logger.error(f"Proxy error: {e}")
            return web.Response(text=str(e), status=500)
    
    def run(self):
        """Run the proxy server"""
        logger.info(f"Starting proxy server on port {self.port}")
        web.run_app(self.app, host='0.0.0.0', port=self.port)


def run_proxy():
    """Entry point for running proxy server"""
    socks_url = os.getenv('SOCKS_PROXY_URL', 'socks5://127.0.0.1:1080')
    http_port = int(os.getenv('HTTP_PROXY_PORT', '8888'))
    
    server = ProxyServer(socks_proxy=socks_url, port=http_port)
    server.run()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run_proxy()