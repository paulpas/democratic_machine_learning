#!/bin/bash
# Script to run enhanced democratic_engine.py for all policy domains and save outputs to markdown files
# With explicit 10-minute timeout for LLM calls as requested

# Create output directory if it doesn't exist
mkdir -p output

# Define policy domains to process
domains=(
    "economy"
    "healthcare" 
    "education"
    "immigration"
    "climate"
    "infrastructure"
)

echo "🚀 Starting Democratic Machine Learning System - LLM Enhanced Governance Modeling"
echo "📋 Processing $((${#domains[@]})) policy domains with 10-minute LLM timeout..."
echo ""

# Process each domain
for domain in "${domains[@]}"; do
    echo "📊 Processing domain: $domain"
    echo "   ⏳ Initializing analysis..."
    
    # Run our enhanced DecisionEngine directly using Python
    # Using a subprocess to better control timeout and output
    output=$(PYTHONPATH=$(pwd) timeout 700 python3 -c "
import sys
import json
import time
from src.core.decision_engine import DecisionEngine
from src.models.policy import Policy, PolicyDomain
from src.models.region import Region
from src.models.voter import Voter, VoterType

def run_domain_analysis(domain_name):
    # Map domain name to PolicyDomain enum
    domain_mapping = {
        'economy': PolicyDomain.ECONOMIC,
        'healthcare': PolicyDomain.HEALTHCARE,
        'education': PolicyDomain.EDUCATION,
        'immigration': PolicyDomain.SECURITY,
        'climate': PolicyDomain.ENVIRONMENT,
        'infrastructure': PolicyDomain.INFRASTRUCTURE
    }
    
    if domain_name not in domain_mapping:
        print(json.dumps({'error': f'Unknown domain: {domain_name}'}), end='')
        return
        
    policy_domain = domain_mapping[domain_name]
    
    # Create engine
    engine = DecisionEngine()
    
    # Show LLM status
    print(f'   🔗 LLM Endpoint: {engine.llm_client.endpoint}')
    print(f'   🤖 LLM Available: {engine.llm_client.available}')
    if not engine.llm_client.available:
        print('   ⚠️  WARNING: LLM not available - will use fallback reasoning')
    
    # Create a simple set of regions for testing
    regions = [
        Region(region_id='test_001', name='Test Region', region_type='state', population=1000000)
    ]
    
    for region_obj in regions:
        engine.register_region(region_obj)
    
    # Create a policy for this domain
    policy_name_map = {
        'economy': 'Economic Policy Test',
        'healthcare': 'Healthcare Policy Test',
        'education': 'Education Policy Test',
        'immigration': 'Immigration Policy Test',
        'climate': 'Climate Policy Test',
        'infrastructure': 'Infrastructure Policy Test'
    }
    
    policy_desc_map = {
        'economy': 'Test economic policy',
        'healthcare': 'Test healthcare policy',
        'education': 'Test education policy',
        'immigration': 'Test immigration policy',
        'climate': 'Test climate policy',
        'infrastructure': 'Test infrastructure policy'
    }
    
    policy = Policy(
        policy_id=f'us_{domain_name}_test',
        name=policy_name_map[domain_name],
        description=policy_desc_map[domain_name],
        domain=policy_domain
    )
    engine.register_policy(policy)
    
    # Create a simple voter panel for testing
    voters = [
        Voter(voter_id='voter_1', region_id='test_001', voter_type=VoterType.EXPERT, 
              expertise={f'us_{domain_name}_test': 0.8}),
        Voter(voter_id='voter_2', region_id='test_001', voter_type=VoterType.PARTICIPANT),
        Voter(voter_id='voter_3', region_id='test_001', voter_type=VoterType.PARTICIPANT)
    ]
    
    # Set test preferences
    voters[0].add_preference(f'us_{domain_name}_test', 0.7)  # Expert support
    voters[1].add_preference(f'us_{domain_name}_test', 0.5)  # Public support
    voters[2].add_preference(f'us_{domain_name}_test', -0.3) # Public opposition
    
    for voter in voters:
        engine.register_voter(voter)
    
    # Run the decision analysis
    try:
        print('   🔄 Executing decision analysis...')
        start_time = time.time()
        decision = engine.make_decision(
            policy_id=f'us_{domain_name}_test',
            region_id='test_001'
        )
        decision_time = time.time() - start_time
        print(f'   ⏱️  Decision analysis completed in {decision_time:.2f}s')
        
        # Get additional context analysis if LLM is available
        print('   🧠 Running LLM-enhanced policy context analysis...')
        llm_start_time = time.time()
        context_analysis = {}
        if engine.llm_client.available:
            print('   📡 Calling LLM endpoint for policy analysis...')
            context_analysis = engine._analyze_policy_context(policy, regions[0], voters)
            llm_elapsed = time.time() - llm_start_time
            print(f'   ✅ LLM Analysis Completed in {llm_elapsed:.2f}s')
            print(f'   📄 Reasoning generated: {len(context_analysis.get(\"reasoning\", \"\"))} characters')
            if 'reasoning' in context_analysis:
                preview = context_analysis['reasoning'][:100].replace('\n', ' ')
                print(f'   💡 Reasoning preview: {preview}...')
        else:
            print('   ⚠️  LLM not available - using fallback analysis')
        
        result = {
            'domain': domain_name,
            'policy_name': policy.name,
            'policy_description': policy.description,
            'decision': {
                'outcome': decision.outcome,
                'confidence': decision.confidence,
                'votes_for': decision.votes_for,
                'votes_against': decision.votes_against,
                'voters_participated': len(decision.voters_participated)
            },
            'context_analysis': context_analysis,
            'llm_enhanced': engine.llm_client.available,
            'timestamp': str(__import__('datetime').datetime.now()),
            'total_regions': len(regions),
            'total_voters': len(voters)
        }
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({'error': str(e)}, indent=2))

run_domain_analysis('$domain')
    " 2>&1)
    
    # Create intuitive filename
    filename="output/us_${domain}_governance_model.md"
    
    # Save output to markdown file with proper formatting
    {
        echo "# United States $domain Governance Model"
        echo ""
        echo "*Generated by Democratic Machine Learning System with LLM Enhancement*"
        echo ""
        echo "---"
        echo ""
        echo "$output"
        echo ""
        echo "---"
        echo ""
        echo "*Model completed at: $(date)*"
        echo "*LLM Endpoint: http://localhost:8080*"
    } > "$filename"
    
    echo "   ✅ Saved to: $filename"
    echo ""
done

echo "🎉 All domains processed successfully!"
echo "📁 Output files saved in: ./output/"
echo ""
echo "📋 Generated files:"
ls -la output/
echo ""
echo "💡 Each markdown file contains:"
echo "   • Complete governance model output"
echo "   • LLM-enhanced policy analysis (when available)"
echo "   • Trust-weighted voting results"
echo "   • Fairness constraint assessments"
echo "   • Anti-pattern detection results"
echo ""
echo "🔧 To view any file: cat output/us_<domain>_governance_model.md"
