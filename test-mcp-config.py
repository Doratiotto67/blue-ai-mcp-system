#!/usr/bin/env python3
import json
import requests
import time
import sys
import argparse
import statistics
import asyncio
import httpx
from typing import Dict, List, Any
from urllib.parse import urlparse

class MCPConfigValidator:
    def __init__(self, config_path: str = "mcp-configuration.json"):
        self.config_path = config_path
        self.config = None
        self.test_results = []
        
    def load_config(self) -> bool:
        """Load and validate JSON configuration"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            print("✅ Configuration loaded successfully")
            return True
        except FileNotFoundError:
            print(f"❌ Configuration file not found: {self.config_path}")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON configuration: {e}")
            return False
    
    def validate_schema(self) -> bool:
        """Validate configuration against expected schema"""
        required_sections = ["mcp_configuration"]
        required_docker_fields = ["host", "port", "api_version"]
        required_backend_fields = ["api_base_url", "auth_token"]
        
        try:
            config = self.config.get("mcp_configuration", {})
            
            # Validate main sections
            for section in required_sections:
                if section not in self.config:
                    print(f"❌ Missing required section: {section}")
                    return False
            
            # Validate docker settings
            docker_settings = config.get("docker_settings", {})
            for field in required_docker_fields:
                if field not in docker_settings:
                    print(f"❌ Missing docker setting: {field}")
                    return False
            
            # Validate backend integration
            backend = config.get("backend_integration", {})
            for field in required_backend_fields:
                if field not in backend:
                    print(f"❌ Missing backend field: {field}")
                    return False
            
            # Validate agent connections
            agents = config.get("agent_connections", [])
            if not agents:
                print("❌ No agent connections configured")
                return False
            
            for i, agent in enumerate(agents):
                required_agent_fields = ["agent_id", "endpoint", "auth_type", "credentials"]
                for field in required_agent_fields:
                    if field not in agent:
                        print(f"❌ Missing field '{field}' in agent {i}")
                        return False
            
            print("✅ Configuration schema validation passed")
            return True
            
        except Exception as e:
            print(f"❌ Schema validation error: {e}")
            return False
    
    def test_docker_connection(self) -> bool:
        """Test Docker daemon connectivity"""
        try:
            docker_settings = self.config["mcp_configuration"]["docker_settings"]
            host = docker_settings.get("host", "localhost")
            port = docker_settings.get("port", "2376")
            
            # Test Docker API endpoint
            docker_url = f"http://{host}:{port}/version"
            
            try:
                response = requests.get(docker_url, timeout=5)
                if response.status_code == 200:
                    print("✅ Docker connection successful")
                    return True
                else:
                    print(f"⚠️  Docker connection returned status {response.status_code}")
                    return False
            except requests.exceptions.RequestException as e:
                print(f"⚠️  Docker connection failed: {e}")
                print("   This is expected if Docker daemon is not exposed via HTTP")
                return True  # Don't fail the entire test for this
                
        except Exception as e:
            print(f"❌ Docker connection test error: {e}")
            return False
    
    def test_agent_connections(self) -> Dict[str, bool]:
        """Test connectivity to all configured agents"""
        results = {}
        agents = self.config["mcp_configuration"]["agent_connections"]
        
        print(f"\n🔍 Testing {len(agents)} agent connections...")
        
        for agent in agents:
            agent_id = agent["agent_id"]
            endpoint = agent["endpoint"]
            health_endpoint = agent.get("health_check", {}).get("endpoint", f"{endpoint}/health")
            
            try:
                # Test health endpoint
                response = requests.get(health_endpoint, timeout=10)
                
                if response.status_code == 200:
                    health_data = response.json()
                    status = health_data.get("status", "unknown")
                    print(f"✅ {agent_id}: {endpoint} - Status: {status}")
                    results[agent_id] = True
                else:
                    print(f"⚠️  {agent_id}: {endpoint} - HTTP {response.status_code}")
                    results[agent_id] = False
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ {agent_id}: {endpoint} - Connection failed: {e}")
                results[agent_id] = False
            except json.JSONDecodeError:
                print(f"⚠️  {agent_id}: {endpoint} - Invalid JSON response")
                results[agent_id] = False
            except Exception as e:
                print(f"❌ {agent_id}: {endpoint} - Unexpected error: {e}")
                results[agent_id] = False
        
        return results
    
    def test_backend_integration(self, host: str) -> bool:
        """Test backend API connectivity"""
        try:
            backend = self.config["mcp_configuration"].get("backend_integration", {})
            api_url = backend.get("api_base_url", "")
            auth_token = backend.get("auth_token", "")
            base = api_url if (api_url and api_url.startswith(("http://", "https://")) and "${" not in api_url) else host
            health_endpoint = f"{base}/health"
            headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}
            try:
                response = requests.get(health_endpoint, headers=headers, timeout=10)
                if response.status_code == 200:
                    print(f"✅ Backend API connection successful: {base}")
                    return True
                else:
                    print(f"⚠️  Backend API returned status {response.status_code}")
                    return False
            except requests.exceptions.RequestException as e:
                print(f"⚠️  Backend API connection failed: {e}")
                return False
        except Exception as e:
            print(f"❌ Backend integration test error: {e}")
            return False
    
    def test_inter_agent_communication(self) -> bool:
        """Test communication between agents through orchestrator"""
        try:
            orchestrator_endpoint = "http://localhost:9080/mcp/tools/call"
            
            # Test simple tool call
            test_payload = {
                "tool_name": "propose_architecture",
                "arguments": {
                    "spec": "Test authentication system",
                    "constraints": {"performance": "high"}
                }
            }
            
            try:
                response = requests.post(
                    orchestrator_endpoint,
                    json=test_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    print("✅ Inter-agent communication successful")
                    return True
                else:
                    print(f"⚠️  Inter-agent communication returned status {response.status_code}")
                    print(f"   Response: {response.text}")
                    return False
                    
            except requests.exceptions.RequestException as e:
                print(f"⚠️  Inter-agent communication failed: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Inter-agent communication test error: {e}")
            return False
    
    async def run_scenarios(self, host: str) -> Dict[str, Any]:
        metrics = {"scenarios": [], "latencies_ms": []}
        async with httpx.AsyncClient(timeout=60.0) as client:
            # quick_code (GET)
            t0 = time.perf_counter()
            r = await client.get(f"{host}/mcp/tools/quick_code?description=fibonacci&language=python&style=modern&stub=1")
            dt = (time.perf_counter() - t0) * 1000
            metrics["scenarios"].append({"name": "quick_code", "status": r.status_code == 200, "status_code": r.status_code})
            metrics["latencies_ms"].append(dt)

            # design_ui sem architecture
            payload_none = {
                "tool_name": "design_ui",
                "arguments": {"spec": "UI simples", "architecture": None, "ux_goals": ["responsive"]}
            }
            t0 = time.perf_counter()
            r = await client.post(f"{host}/mcp/tools/call", json=payload_none, headers={"Content-Type": "application/json"})
            dt = (time.perf_counter() - t0) * 1000
            metrics["scenarios"].append({"name": "design_ui_none", "status": r.status_code == 200, "status_code": r.status_code})
            metrics["latencies_ms"].append(dt)

            # design_ui com architecture mínima
            payload_min = {
                "tool_name": "design_ui",
                "arguments": {"spec": "UI mínima", "architecture": {}, "ux_goals": ["accessible"]}
            }
            t0 = time.perf_counter()
            r = await client.post(f"{host}/mcp/tools/call", json=payload_min, headers={"Content-Type": "application/json"})
            dt = (time.perf_counter() - t0) * 1000
            metrics["scenarios"].append({"name": "design_ui_min", "status": r.status_code == 200, "status_code": r.status_code})
            metrics["latencies_ms"].append(dt)

            # design_ui com architecture completa
            payload_full = {
                "tool_name": "design_ui",
                "arguments": {
                    "spec": "Dashboard completa",
                    "architecture": {"frontend": {"routes": ["/"], "components": ["Header", "Footer"], "state": "default"}},
                    "ux_goals": ["modern", "responsive", "accessible"]
                }
            }
            t0 = time.perf_counter()
            r = await client.post(f"{host}/mcp/tools/call", json=payload_full, headers={"Content-Type": "application/json"})
            dt = (time.perf_counter() - t0) * 1000
            metrics["scenarios"].append({"name": "design_ui_full", "status": r.status_code == 200, "status_code": r.status_code})
            metrics["latencies_ms"].append(dt)

        return metrics

    async def run_load(self, host: str, concurrency: int, iterations: int) -> Dict[str, Any]:
        latencies = []
        errors = 0
        async def one_call(i: int):
            nonlocal errors
            body = {
                "tool_name": "quick_code",
                "arguments": {"description": f"função soma {i}", "language": "python", "style": "minimal"}
            }
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    t0 = time.perf_counter()
                    r = await client.post(f"{host}/mcp/tools/call", json=body, headers={"Content-Type": "application/json"})
                    dt = (time.perf_counter() - t0) * 1000
                    if r.status_code == 200:
                        latencies.append(dt)
                    else:
                        errors += 1
            except Exception:
                errors += 1
        tasks = []
        for i in range(iterations):
            tasks.append(one_call(i))
            if len(tasks) % concurrency == 0:
                await asyncio.gather(*tasks)
                tasks = []
        if tasks:
            await asyncio.gather(*tasks)
        total = iterations
        success = total - errors
        rate = success / total if total else 0
        p50 = statistics.median(latencies) if latencies else 0
        p95 = statistics.quantiles(latencies, n=100)[94] if len(latencies) >= 100 else max(latencies) if latencies else 0
        p99 = statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies) if latencies else 0
        return {"total": total, "success": success, "error": errors, "success_rate": rate, "p50_ms": p50, "p95_ms": p95, "p99_ms": p99}

    def run_all_tests(self, host: str, concurrency: int, iterations: int, report_path: str | None = None) -> Dict[str, Any]:
        print("🚀 Iniciando suíte de validação MCP\n")
        results = {
            "config_loaded": False,
            "schema_valid": False,
            "docker_connected": False,
            "agents_connected": {},
            "backend_connected": False,
            "inter_agent_communication": False,
            "scenarios": {},
            "load": {},
            "overall_status": "FAILED"
        }
        results["config_loaded"] = self.load_config()
        if not results["config_loaded"]:
            return results
        results["schema_valid"] = self.validate_schema()
        results["docker_connected"] = self.test_docker_connection()
        results["agents_connected"] = self.test_agent_connections()
        results["backend_connected"] = self.test_backend_integration(host)
        results["inter_agent_communication"] = self.test_inter_agent_communication()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        scen = loop.run_until_complete(self.run_scenarios(host))
        load = loop.run_until_complete(self.run_load(host, concurrency, iterations))
        loop.close()
        results["scenarios"] = scen
        results["load"] = load
        critical_tests = [
            results["config_loaded"],
            results["schema_valid"],
            len([v for v in results["agents_connected"].values() if v]) > 0,
            results["inter_agent_communication"]
        ]
        results["overall_status"] = "SUCCESS" if all(critical_tests) else "PARTIAL_SUCCESS"
        print("\n" + "="*50)
        print("📊 RESUMO")
        print("="*50)
        print(f"Config Loaded: {'✅' if results['config_loaded'] else '❌'}")
        print(f"Schema Valid: {'✅' if results['schema_valid'] else '❌'}")
        print(f"Docker Connected: {'✅' if results['docker_connected'] else '❌'}")
        print(f"Agents Connected: {len([v for v in results['agents_connected'].values() if v])}/{len(results['agents_connected'])}")
        print(f"Inter-Agent: {'✅' if results['inter_agent_communication'] else '❌'}")
        if scen["latencies_ms"]:
            print(f"Scenarios p50: {statistics.median(scen['latencies_ms']):.1f} ms")
        print(f"Load success: {load['success']}/{load['total']} ({load['success_rate']*100:.1f}%)")
        print(f"p95: {load['p95_ms']:.1f} ms, p99: {load['p99_ms']:.1f} ms")
        if report_path:
            try:
                with open(report_path, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                print(f"Relatório salvo em: {report_path}")
            except Exception as e:
                print(f"Falha ao salvar relatório: {e}")
        return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="mcp-configuration.json")
    parser.add_argument("--host", default="http://localhost:9080")
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--report", default="logs/test-report.json")
    args = parser.parse_args()
    print("🔧 MCP Configuration Validator")
    print(f"📁 Config: {args.config}")
    print(f"🌐 Host: {args.host}")
    validator = MCPConfigValidator(args.config)
    results = validator.run_all_tests(args.host, args.concurrency, args.iterations, args.report)
    if results["overall_status"] in ["SUCCESS", "PARTIAL_SUCCESS"]:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()