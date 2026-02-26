/**
 * AXCTL Token Savings Calculator
 * Interactive widget for landing page - TOKEN BASED
 */

// Constants
const AXCTL_EFFICIENCY = 0.0192; // AXCTL uses 1.92% of tokens vs Vision AI (150/7800)
const TIME_SAVINGS_HOURS = 30;    // Hours saved per year
const HOURLY_RATE = 100;          // $/hour developer billing rate

// Update slider value display
const tokensSlider = document.getElementById('tokens-slider');
const tokensValue = document.getElementById('tokens-value');

if (tokensSlider && tokensValue) {
  tokensSlider.addEventListener('input', function() {
    const value = parseInt(this.value);
    // Format with K/M suffix
    if (value >= 1000000) {
      tokensValue.textContent = (value / 1000000).toFixed(1) + 'M';
    } else if (value >= 1000) {
      tokensValue.textContent = (value / 1000).toFixed(0) + 'K';
    } else {
      tokensValue.textContent = value.toLocaleString();
    }
    calculate();
  });
}

// Auto-calculate when token cost changes
const tokenCostInput = document.getElementById('token-cost');
if (tokenCostInput) {
  tokenCostInput.addEventListener('input', calculate);
}

// Calculate savings
function calculate() {
  // Get inputs
  const tokensPerMonth = parseInt(document.getElementById('tokens-slider').value);
  const tokenCostPer1M = parseFloat(document.getElementById('token-cost').value);
  
  // Calculate token costs for Vision AI approach
  const vlmTokensPerMonth = tokensPerMonth;
  const vlmTokensPerYear = vlmTokensPerMonth * 12;
  
  // Calculate AXCTL token usage (98% more efficient)
  const axctlTokensPerMonth = tokensPerMonth * AXCTL_EFFICIENCY;
  const axctlTokensPerYear = axctlTokensPerMonth * 12;
  
  // Convert to dollars
  const vlmCostPerMonth = (vlmTokensPerMonth / 1000000) * tokenCostPer1M;
  const axctlCostPerMonth = (axctlTokensPerMonth / 1000000) * tokenCostPer1M;
  
  const vlmCostPerYear = vlmCostPerMonth * 12;
  const axctlCostPerYear = axctlCostPerMonth * 12;
  
  // Calculate savings
  const tokenSavings = vlmCostPerYear - axctlCostPerYear;
  const timeSavings = TIME_SAVINGS_HOURS * HOURLY_RATE;
  const totalValue = tokenSavings + timeSavings;
  
  // Calculate ROI percentage
  const roiPercent = ((tokenSavings / vlmCostPerYear) * 100).toFixed(0);
  
  // Format token amounts for display
  const formatTokens = (tokens) => {
    if (tokens >= 1000000) return (tokens / 1000000).toFixed(1) + 'M';
    if (tokens >= 1000) return (tokens / 1000).toFixed(0) + 'K';
    return tokens.toLocaleString();
  };
  
  // Update display
  document.getElementById('vlm-tokens').textContent = formatTokens(vlmTokensPerMonth);
  document.getElementById('vlm-cost').textContent = vlmCostPerMonth.toFixed(2);
  document.getElementById('vlm-cost-year').textContent = vlmCostPerYear.toFixed(2);
  
  document.getElementById('axctl-tokens').textContent = formatTokens(axctlTokensPerMonth);
  document.getElementById('axctl-cost').textContent = axctlCostPerMonth.toFixed(2);
  document.getElementById('axctl-cost-year').textContent = axctlCostPerYear.toFixed(2);
  
  document.getElementById('savings').textContent = tokenSavings.toFixed(2);
  document.getElementById('roi-percent').textContent = roiPercent;
  
  document.getElementById('total-value').textContent = Math.round(totalValue).toLocaleString();
  
  return {
    vlmTokensPerMonth,
    vlmCostPerMonth,
    vlmCostPerYear,
    axctlTokensPerMonth,
    axctlCostPerMonth,
    axctlCostPerYear,
    tokenSavings,
    timeSavings,
    totalValue,
    roiPercent
  };
}

// Run calculation on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', calculate);
} else {
  calculate();
}

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { calculate };
}
