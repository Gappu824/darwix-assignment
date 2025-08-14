"""CLI interface for Digital Skeptic AI"""

import asyncio
import argparse
import sys
import json
from datetime import datetime
from typing import Optional

from src.models.schemas import AnalysisRequest
from src.core.orchestrator import orchestrator
from src.utils.config import config

def print_banner():
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                     DIGITAL SKEPTIC AI                      ║
║          Empowering Critical Thinking in an Age of          ║
║                    Information Overload                     ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)

def print_progress(message: str, status: str = "INFO"):
    """Print progress message with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    status_emoji = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "ERROR": "❌",
        "WARNING": "⚠️"
    }
    emoji = status_emoji.get(status, "📍")
    print(f"[{timestamp}] {emoji} {message}")

async def analyze_url(url: str, options: dict) -> bool:
    """Analyze a single URL"""
    
    print_progress(f"Starting analysis of: {url}")
    
    try:
        # Create analysis request
        request = AnalysisRequest(
            url=url,
            include_counter_narrative=options.get('include_counter_narrative', True),
            include_entity_analysis=options.get('include_entity_analysis', True),
            include_source_check=options.get('include_source_check', True)
        )
        
        # Execute analysis
        result = await orchestrator.analyze_article(request)
        
        if result.success:
            print_progress(f"Analysis completed in {result.processing_time:.2f} seconds", "SUCCESS")
            
            # Output results
            if options.get('output_format') == 'json':
                output_json(result, options.get('output_file'))
            else:
                output_markdown(result, options.get('output_file'))
            
            # Print summary to console
            print_summary(result)
            
            return True
            
        else:
            print_progress(f"Analysis failed: {result.error}", "ERROR")
            return False
            
    except Exception as e:
        print_progress(f"Error: {str(e)}", "ERROR")
        return False

def output_markdown(result, output_file: Optional[str] = None):
    """Output results as markdown"""
    
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result.markdown_report)
            print_progress(f"Markdown report saved to: {output_file}", "SUCCESS")
        except Exception as e:
            print_progress(f"Failed to save markdown report: {e}", "ERROR")
    else:
        print("\n" + "="*80)
        print("ANALYSIS REPORT")
        print("="*80)
        print(result.markdown_report)

def output_json(result, output_file: Optional[str] = None):
    """Output results as JSON"""
    
    # Convert result to JSON-serializable format
    result_dict = {
        "success": result.success,
        "processing_time": result.processing_time,
        "article": {
            "url": result.result.article.url,
            "title": result.result.article.title,
            "domain": result.result.article.domain,
            "author": result.result.article.author,
            "publish_date": result.result.article.publish_date,
            "quality_score": result.result.article.quality_score
        },
        "analysis": {
            "bias_confidence": result.result.bias_confidence,
            "overall_credibility": result.result.overall_credibility,
            "claims_count": len(result.result.core_claims),
            "red_flags_count": len(result.result.red_flags),
            "verification_questions_count": len(result.result.verification_questions)
        }
    }
    
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, indent=2, ensure_ascii=False)
            print_progress(f"JSON report saved to: {output_file}", "SUCCESS")
        except Exception as e:
            print_progress(f"Failed to save JSON report: {e}", "ERROR")
    else:
        print("\n" + "="*80)
        print("ANALYSIS RESULTS (JSON)")
        print("="*80)
        print(json.dumps(result_dict, indent=2, ensure_ascii=False))

def print_summary(result):
    """Print a brief summary to console"""
    
    analysis = result.result
    
    print("\n" + "="*60)
    print("📊 ANALYSIS SUMMARY")
    print("="*60)
    
    print(f"📰 Article: {analysis.article.title or 'Unknown Title'}")
    print(f"🌐 Domain: {analysis.article.domain}")
    print(f"⭐ Quality Score: {analysis.article.quality_score:.1%}")
    print(f"🎯 Credibility: {analysis.overall_credibility:.1%}")
    print(f"⚖️  Bias Level: {analysis.bias_confidence:.1%}")
    
    print(f"\n📋 Analysis Results:")
    print(f"   • Core Claims: {len(analysis.core_claims)}")
    print(f"   • Red Flags: {len(analysis.red_flags)}")
    print(f"   • Verification Questions: {len(analysis.verification_questions)}")
    
    if analysis.entities:
        print(f"   • Key Entities: {len(analysis.entities)}")
    
    # Show top red flags
    high_severity_flags = [f for f in analysis.red_flags if f.severity.value == "high"]
    if high_severity_flags:
        print(f"\n🚩 High-Severity Issues: {len(high_severity_flags)}")
        for flag in high_severity_flags[:3]:
            print(f"   • {flag.description}")
    
    print("="*60)

async def test_url(url: str):
    """Test URL accessibility"""
    
    print_progress(f"Testing URL accessibility: {url}")
    
    try:
        diagnostics = await orchestrator.test_url(url)
        
        print("\n" + "="*60)
        print("🔍 URL DIAGNOSTICS")
        print("="*60)
        
        print(f"URL: {diagnostics['url']}")
        print(f"Accessible: {'✅ Yes' if diagnostics['accessible'] else '❌ No'}")
        
        if diagnostics['status_code']:
            print(f"Status Code: {diagnostics['status_code']}")
        
        if diagnostics['content_type']:
            print(f"Content Type: {diagnostics['content_type']}")
        
        if diagnostics['is_news_site']:
            print("✅ Appears to be a news site")
        else:
            print("⚠️  May not be a news site")
        
        if diagnostics['error']:
            print(f"❌ Error: {diagnostics['error']}")
        
        if diagnostics['recommendations']:
            print("\n💡 Recommendations:")
            for rec in diagnostics['recommendations']:
                print(f"   • {rec}")
        
        print("="*60)
        
    except Exception as e:
        print_progress(f"Test failed: {str(e)}", "ERROR")

async def preview_url(url: str):
    """Preview URL content"""
    
    print_progress(f"Getting preview for: {url}")
    
    try:
        preview = await orchestrator.quick_preview(url)
        
        print("\n" + "="*60)
        print("👀 CONTENT PREVIEW")
        print("="*60)
        
        if preview.get('title'):
            print(f"Title: {preview['title']}")
        
        if preview.get('domain'):
            print(f"Domain: {preview['domain']}")
        
        if preview.get('author'):
            print(f"Author: {preview['author']}")
        
        if preview.get('estimated_length'):
            print(f"Content Length: {preview['estimated_length']} characters")
        
        if preview.get('quality_score'):
            print(f"Quality Score: {preview['quality_score']:.1%}")
        
        if preview.get('extraction_method'):
            print(f"Extraction Method: {preview['extraction_method']}")
        
        if preview.get('content_preview'):
            print(f"\nContent Preview:")
            print("-" * 40)
            print(preview['content_preview'])
            print("-" * 40)
        
        if preview.get('issues'):
            print(f"\n⚠️  Issues:")
            for issue in preview['issues']:
                print(f"   • {issue}")
        
        print("="*60)
        
    except Exception as e:
        print_progress(f"Preview failed: {str(e)}", "ERROR")

def main():
    """Main CLI entry point"""
    
    parser = argparse.ArgumentParser(
        description="Digital Skeptic AI - News Article Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py analyze https://example.com/article
  python main.py analyze https://example.com/article --output report.md
  python main.py analyze https://example.com/article --format json --output results.json
  python main.py test https://example.com/article
  python main.py preview https://example.com/article
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze an article')
    analyze_parser.add_argument('url', help='URL of the article to analyze')
    analyze_parser.add_argument('--output', '-o', help='Output file path')
    analyze_parser.add_argument('--format', '-f', choices=['markdown', 'json'], 
                               default='markdown', help='Output format')
    analyze_parser.add_argument('--no-counter', action='store_true', 
                               help='Skip counter-narrative generation')
    analyze_parser.add_argument('--no-entities', action='store_true', 
                               help='Skip entity analysis')
    analyze_parser.add_argument('--no-source-check', action='store_true', 
                               help='Skip source credibility check')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test URL accessibility')
    test_parser.add_argument('url', help='URL to test')
    
    # Preview command
    preview_parser = subparsers.add_parser('preview', help='Preview article content')
    preview_parser.add_argument('url', help='URL to preview')
    
    args = parser.parse_args()
    
    if not args.command:
        print_banner()
        parser.print_help()
        return 1
    
    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        print_progress(f"Configuration error: {e}", "ERROR")
        print("Please check your environment variables.")
        return 1
    
    print_banner()
    
    # Execute command
    if args.command == 'analyze':
        options = {
            'output_file': args.output,
            'output_format': args.format,
            'include_counter_narrative': not args.no_counter,
            'include_entity_analysis': not args.no_entities,
            'include_source_check': not args.no_source_check
        }
        
        success = asyncio.run(analyze_url(args.url, options))
        return 0 if success else 1
        
    elif args.command == 'test':
        asyncio.run(test_url(args.url))
        return 0
        
    elif args.command == 'preview':
        asyncio.run(preview_url(args.url))
        return 0
    
    return 1

if __name__ == "__main__":
    sys.exit(main()) 
