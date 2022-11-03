%%% Created by Tom Liu %%%
%%% 2022 November%%%

%%% The function fits two lines to a set of (x,y) datapoints,
%%% one horizontal, one vertical. If any of the checked  
%%% points that do not fit to either of the two lines,
%%% the function returns true
%%% The vertical line must also be on the right side of the 
%%% horizontal line.
%%% All vals must also be positive.

% x = rdet, y = pj
% returns whether to cut the curve, if not, then the average
% y value of the horizontal line, if so, then avgPVal = -1
function [doCut avgPVal] = filter_loadcurve(rdet, pj)
    % someone can make these function parameters if they care enough
    
    % number of points to check for flatness of line
    num_check = 25;
    % only check the middle 60 percent of the curve
    start_frac = 0.2;
    end_frac = 0.8;
    % cut anything not within 10 percent of average value
    check_thresh = 0.1;

    
    if(length(rdet) < 10 || length(rdet)~=length(pj))
        doCut = true;
        avgPVal = -1;
        return;
    end

    min_xs = min(rdet);
    max_xs = max(rdet);
    min_ys = min(pj);
    max_ys = max(pj);

    check_xs = linspace(start_frac*(max_xs-min_xs) + min_xs,...
                            end_frac*(max_xs-min_xs) + min_xs, num_check);
    check_ys = linspace(start_frac*(max_ys-min_ys) + min_ys,...
                            end_frac*(max_ys-min_ys) + min_ys, num_check);
    % interpolate does not take in nan values
    rdet(isnan(rdet)) = -1;
    pj(isnan(pj)) = -1;

    horiz_line = interp1(rdet, pj, check_xs);
    vert_line = interp1(pj, rdet, check_ys);
    
    avgPVal = mean(horiz_line);
    avgx = mean(vert_line);
    
    %%%%% For Debugging %%%%%
    %disp(avgPVal);
    %disp(avgx);
    %disp(max(horiz_line));
    %disp(min(horiz_line));
    %disp(max(vert_line));
    %disp(min(vert_line));
    %%%%%
    if(max(horiz_line)/avgPVal > 1+check_thresh | ...
        min(horiz_line)/avgPVal < 1-check_thresh | ...
        max(vert_line)/avgx > 1+check_thresh | ...
        min(vert_line)/avgx < 1-check_thresh | ...
        avgx < check_xs(num_check) | ...
        avgPVal < 0 | avgx < 0)

        doCut = true;
        avgPVal = -1;
    else
        doCut = false;
    
    end


end


