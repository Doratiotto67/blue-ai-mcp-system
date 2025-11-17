#!/usr/bin/env python3
"""
Script de teste para validar a integração do Memory Agent
com os 3 modelos LLM e o sistema de fallback.
"""

import asyncio
import json
import httpx
import logging
from datetime import datetime
from typing import Dict, Any

# Configura logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MemoryIntegrationTester:
    """Testador de integração do sistema de memória."""
    
    def __init__(self, base_url: str = "http://localhost:9080"):
        self.orchestrator_url = base_url
        self.memory_url = "http://localhost:9086"
        self.timeout = 30.0
        
    async def test_memory_agent_health(self) -> bool:
        """Testa health check do Memory Agent."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(f"{self.memory_url}/health")
                if resp.status_code == 200:
                    data = resp.json()
                    logger.info(f"✅ Memory Agent health: {data}")
                    return True
                else:
                    logger.error(f"❌ Memory Agent health failed: {resp.status_code}")
                    return False
        except Exception as e:
            logger.error(f"❌ Memory Agent health error: {e}")
            return False
    
    async def test_store_experience(self) -> bool:
        """Testa armazenamento de experiência."""
        try:
            experience = {
                "project_id": "test-project",
                "module": "test-module",
                "stack": "python+fastapi+react",
                "severity": "high",
                "error_type": "security",
                "summary": "Test experience: SQL injection vulnerability",
                "root_cause": "Direct string concatenation in SQL query",
                "fix_applied": "Use parameterized queries with SQLAlchemy",
                "bad_snippet": "query = f'SELECT * FROM users WHERE id = {user_id}'",
                "good_snippet": "query = text('SELECT * FROM users WHERE id = :user_id')",
                "tags": ["security", "sql", "injection"],
                "affected_components": ["auth", "database"]
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.memory_url}/mcp",
                    json={
                        "tool_name": "store_experience",
                        "arguments": experience
                    }
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    result = data.get("result", {})
                    experience_id = result.get("content")
                    if experience_id:
                        logger.info(f"✅ Experience stored: {experience_id}")
                        return True
                
                logger.error(f"❌ Store experience failed: {resp.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Store experience error: {e}")
            return False
    
    async def test_lessons_retrieval(self) -> bool:
        """Testa recuperação de lições aprendidas."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.memory_url}/mcp",
                    json={
                        "tool_name": "lessons_for_task",
                        "arguments": {
                            "spec": "Create user authentication API with JWT",
                            "stack": "python+fastapi+react",
                            "limit": 5
                        }
                    }
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    result = data.get("result", {})
                    lessons = result.get("content", {})
                    
                    total_lessons = lessons.get("total_lessons", 0)
                    logger.info(f"✅ Retrieved {total_lessons} lessons")
                    
                    if total_lessons > 0:
                        logger.info(f"📚 High-level rules: {len(lessons.get('high_level_rules', []))}")
                        logger.info(f"🔍 Code smells: {len(lessons.get('code_smells_to_avoid', []))}")
                        logger.info(f"🔒 Security pitfalls: {len(lessons.get('security_pitfalls', []))}")
                    
                    return True
                
                logger.error(f"❌ Lessons retrieval failed: {resp.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Lessons retrieval error: {e}")
            return False
    
    async def test_memory_stats(self) -> bool:
        """Testa estatísticas da memória."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.memory_url}/mcp",
                    json={
                        "tool_name": "memory_stats",
                        "arguments": {}
                    }
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    result = data.get("result", {})
                    stats = result.get("content", {})
                    
                    logger.info(f"✅ Memory stats retrieved:")
                    logger.info(f"   📊 Total experiences: {stats.get('total_experiences', 0)}")
                    logger.info(f"   📈 Memory hit rate: {stats.get('memory_hit_rate', 0):.2%}")
                    logger.info(f"   🔄 Lesson reuse rate: {stats.get('lesson_reuse_rate', 0):.2f}")
                    
                    return True
                
                logger.error(f"❌ Memory stats failed: {resp.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Memory stats error: {e}")
            return False
    
    async def test_deduplication(self) -> bool:
        """Testa deduplicação de experiências."""
        try:
            # Primeiro, armazena experiências duplicadas
            duplicate_experiences = [
                {
                    "project_id": "test-dup",
                    "module": "auth",
                    "stack": "python+fastapi",
                    "severity": "critical",
                    "error_type": "security",
                    "summary": "SQL injection vulnerability in login",
                    "root_cause": "Direct SQL concatenation",
                    "fix_applied": "Use parameterized queries"
                },
                {
                    "project_id": "test-dup",
                    "module": "auth",
                    "stack": "python+fastapi",
                    "severity": "critical",
                    "error_type": "security",
                    "summary": "SQL injection vulnerability in login endpoint",
                    "root_cause": "Direct SQL string concatenation",
                    "fix_applied": "Use parameterized queries with SQLAlchemy"
                }
            ]
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Armazena duplicatas
                for exp in duplicate_experiences:
                    await client.post(
                        f"{self.memory_url}/mcp",
                        json={
                            "tool_name": "store_experience",
                            "arguments": exp
                        }
                    )
                
                # Executa deduplicação
                resp = await client.post(
                    f"{self.memory_url}/mcp",
                    json={
                        "tool_name": "deduplicate_experiences",
                        "arguments": {}
                    }
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    result = data.get("result", {})
                    dedup_result = result.get("content", {})
                    
                    logger.info(f"✅ Deduplication completed:")
                    logger.info(f"   🗑️  Duplicates found: {dedup_result.get('duplicates_found', 0)}")
                    logger.info(f"   🗑️  Duplicates removed: {dedup_result.get('duplicates_removed', 0)}")
                    logger.info(f"   💾 Experiences kept: {dedup_result.get('experiences_kept', 0)}")
                    
                    return True
                
                logger.error(f"❌ Deduplication failed: {resp.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Deduplication error: {e}")
            return False
    
    async def test_orchestrator_integration(self) -> bool:
        """Testa integração com o Orchestrator."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.orchestrator_url}/mcp/tools/call",
                    json={
                        "tool_name": "get_memory_stats",
                        "arguments": {}
                    }
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    result = data.get("result", {})
                    
                    if result:
                        logger.info("✅ Orchestrator integration successful")
                        return True
                
                logger.error(f"❌ Orchestrator integration failed: {resp.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Orchestrator integration error: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Executa todos os testes e retorna resultados."""
        logger.info("🚀 Starting Memory Agent integration tests...")
        logger.info("=" * 60)
        
        tests = {
            "Memory Agent Health": self.test_memory_agent_health,
            "Store Experience": self.test_store_experience,
            "Lessons Retrieval": self.test_lessons_retrieval,
            "Memory Stats": self.test_memory_stats,
            "Deduplication": self.test_deduplication,
            "Orchestrator Integration": self.test_orchestrator_integration,
        }
        
        results = {}
        
        for test_name, test_func in tests.items():
            logger.info(f"\n🧪 Running: {test_name}")
            try:
                results[test_name] = await test_func()
                status = "✅ PASSED" if results[test_name] else "❌ FAILED"
                logger.info(f"   Status: {status}")
            except Exception as e:
                logger.error(f"   ❌ ERROR: {e}")
                results[test_name] = False
        
        # Resumo final
        logger.info("\n" + "=" * 60)
        logger.info("📊 TEST RESULTS SUMMARY")
        logger.info("=" * 60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, passed_test in results.items():
            status = "✅" if passed_test else "❌"
            logger.info(f"{status} {test_name}")
        
        logger.info(f"\n📈 Overall: {passed}/{total} tests passed ({passed/total:.1%})")
        
        if passed == total:
            logger.info("🎉 All tests passed! Memory Agent is ready for production.")
        else:
            logger.warning("⚠️  Some tests failed. Please check the issues above.")
        
        return results


async def main():
    """Função principal."""
    tester = MemoryIntegrationTester()
    
    # Espera um pouco para os serviços iniciarem
    logger.info("⏳ Waiting for services to start...")
    await asyncio.sleep(5)
    
    # Executa testes
    results = await tester.run_all_tests()
    
    # Salva resultados
    timestamp = datetime.now().isoformat()
    report = {
        "timestamp": timestamp,
        "results": results,
        "summary": {
            "total": len(results),
            "passed": sum(1 for r in results.values() if r),
            "failed": sum(1 for r in results.values() if not r)
        }
    }
    
    with open("logs/memory_integration_test.json", "w") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"📄 Test report saved to logs/memory_integration_test.json")
    
    # Exit code
    exit_code = 0 if all(results.values()) else 1
    exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())