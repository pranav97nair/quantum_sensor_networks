%%  First published by Sean William Moore 2024-06, © CC 4.0

%Please cite:
%   Sean William Moore and Jacob Andrew Dunningham. Secure quantum-enhanced measurements on a network of sensors. 2024. arXiv: 2406.19285 [quant-ph]. url: https://arxiv.org/abs/2406.19285


function [mu,nu,mse,var,bias2,rBar] = circStats(position,weight,trueValue)
%circStats finds the circular statistics of the input distributions

%input:
%   position        positions of data points
%   weight          weights of data points
%   trueValue       true value that data is drawn from

%output:
%   mu              circular mean [0,2pi)
%   nu              circular standard deviation [0,infty)
%   mse             circular mean square error [0,2]
%   var             circular variance [0,1]
%   bias2           circular bias squared [0,2]
%   rBar            circular mean resultant length [0,1]

%further information:
%   mse = var + bias2
%   var and nu approximate their linear equivalents for narrow distributions. nu more strictly.

%   K. V. Mardia and P. E. Jupp, Directional Statistics, edited by K. V. Mardia and P. E. Jupp, Wiley Series in Probability and
%   Statistics (John Wiley & Sons, Chichester, England, 1999).

if isempty(weight) 
    %no weighting specified, likely that data is unbinned measurement
    %results on circle.
    weight = ones(size(position));
end

if length(position) ~= numel(position)
    error('circStats position has too many dimensions')
end

if isempty(trueValue)
    %value around which to calculate mse and bias2 not defined, set to 0
    trueValue = 0;
end

if size(weight) ~= size(position)
    [sW1,sW2] = size(weight);
    [sP1,sP2] = size(position);
    if sW1 == sP2 && sW2 == sP1
        weight = permute(weight , [2 1]);
    end
end

%weighted sum of cos and sin of angles
r = sum(weight.*exp(1i*position));
%mean direction
mu = mod(angle(r),2*pi);
%mean resultant length
rBar = abs(r)/sum(weight);
%dispersion defined as a function of mean resultant length
nu = sqrt(-2*log(rBar));
mse = sum( (1-cos(position-trueValue)) .*weight ) / sum(weight);
var = 1-rBar;
bias2 = 2*rBar*sin( (mu-trueValue)/2 )^2;

end

