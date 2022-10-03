#!/usr/bin/perl

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# OpenSource Foosball Tournament Software
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# For this script to work you need the Imager and Imager::Graph
#     libraries from CPAN installed.
# You then just throw this file in your cgi directory,
#	along with the foosball.data file and the ImUgly.ttf
#	font file.
# Make sure that the foosball.data, foosball.html, and foosball.jpg
#	files are all owned by nobody.nobody (or apache.apache)
#	and are writable.
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

# Include strict debugging, and any other dependencies.
use strict;
use CGI qw(:standard);
use Imager::Graph::Pie;

# Initialize main program variables
my ($filename, $htmlfile, $jpgfile) = '';
my (%names, %rank, %wins, %losses, %point_total, %games, %average, 
	%delta, %streak, @players) = ();

# Load in the user specified default values...
scalar eval `cat tourney.cfg`;

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Main Logic of program
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

# Read STDIN for new data / or read CGI paramaters
# if being run from a browser...
my $data = ReadNewData( $filename );

# Append new data to data file
($data) and WriteNewData( $filename, $data );

# Calculate player statistics
my ($games, $won, $lost, $last) = CalculateStats( $filename );

# Create an updated web page
CreateWebPage( $htmlfile, $games, $won, $lost, $last);

# Output errors/results or redirect
# to that page if run from a browser.
($ARGV[0] eq '') and RedirectWebPage();

exit;

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# 	SUBROUTINES begin here.
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

# =-=-=-=-=-=-=
# ReadNewData
# =-=-=-=-=-=-=
# Input: $file (full path to data file)
# Output: $data (4 names and 2 scores in a comma separated list)
#
sub ReadNewData{
    my $file = shift;
    my $data = '';

    # Read from STDIN
    if ($ARGV[0]) { #This means we are adding data
        $data = $ARGV[0];
        chomp $data;
    }

    # Ok, cmd=new entered, let's output a web page 
    # suitable for data entry...
    elsif (param('cmd') eq 'new') {
        CreateInputWebPage();
	exit;
    }
    
    # Read from CGI parameters
    elsif (param('winner1')) {
        $data = (param('winner1')) . ',' .
 		(param('winner2')) . ',' .
 		(param('loser1')) . ',' .
 		(param('loser2')) . ',' .
 		(param('score1')) . ',' .
 		(param('score2'));
    }
    
    # No data entered, let's try having it take you to the edit screen.
    else {
        CreateInputWebPage();
	exit;
    }
    
    # If we have data, then test it.
    if ($data ne '') {
        foreach(@players) {
            $names{$_} = 1;
        }
	
        my @inputs = split(',',$data);
        ($#inputs == 5) or OutputError("You MUST enter 4 names followed by 2 scores: Winner,Winner,Loser,Loser,Winning score,Losing score.\n\nAllowed names are: \n\n" . join("\n",@players));
	
	# The last two inputs are the score.
	my $score2 = pop @inputs;
	my $score1 = pop @inputs;
	
	# Test for valid score
	(($score1-1)>$score2) or OutputError("Score of $score1-$score2 is not valid, must win by two.");
	
	# Test for valid player names
        foreach (@inputs) {
	    ($names{$_}) or OutputError("$_ is not a valid name.  Valid names are: \n\n\n". join("\n",@players));
	}
        ($ARGV[0] ne '') and print "\n\nGame added for: $data\nNow updating the website...\n\n";
    }
    
    # Add a date signature to each game    
    $data .= ','.time;
    
    # If we made it here, we've got good data, return true.
    return ($data);
}

# =-=-=-=-=-=
# WriteNewData
# =-=-=-=-=-=
# Input: $file (full path to data file)
#	 $data (4 names in a comma separated list)
# Output: None.
#
sub WriteNewData{
    my $file = shift;
    my $data = shift;
    
    open(GAMES, ">>$file");
    print GAMES $data,"\n";
    close(GAMES);
}

# =-=-=-=-=-=
# ReadData
# =-=-=-=-=-=
# Input:  $file (full path to data file)
# Output: @data (array of 4 names and 2 
#	scores in a comma separated list)
#
sub ReadData{
    my $file = shift;
    my @data;
    
    open(GAMES, "<$file");
    while (<GAMES>) {
    	chomp($_);  		# Eliminate whitespace
	push(@data, $_);	# Push the data
    }
    close(GAMES);

    # This really should just be an array reference.
    return(@data);
}

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Calculate various statistics.
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
sub CalculateStats{
    my $file = shift;

    # Initialize the player's statistics
    foreach (@players) {
        $point_total{$_} = 0;
	$games{$_}	= 0;
        $wins{$_} 	= 0;
        $losses{$_} 	= 0;
        $streak{$_} 	= 0;
    }

    my (@games) = ReadData( $filename );
    my $number_of_games = ($#games)+1;
	
    my ($winner1, $winner2, $loser1, $loser2, $score1, $score2) 
    		= split (',',$games[$#games]);
    
    # Text formatted to display the last game processed.
    my $lastgame = "<b>$winner1</b> and <b>$winner2</b> VS.".
    		   "<b>$loser1</b> and <b>$loser2</b> - Score: $score1-$score2";
    my $current_game = 1;

    foreach (@games) {
        ($winner1, $winner2, $loser1, $loser2, $score1, $score2) = split (',',$_);
        my %player_rank = reverse %rank;
        my $handicap = $player_rank{$winner1} + $player_rank{$winner2}
		     - $player_rank{$loser1}  - $player_rank{$loser2};
        my $game_value = 20 + $handicap;

        # Change the hash values based on winner/loser
	
	# Adjust wins / loses
        $wins{$winner1} +=1;
        $wins{$winner2} +=1;
        $losses{$loser1} +=1;
        $losses{$loser2} +=1;
	
	# Add points for each game to cumulative player score
        $point_total{$winner1} += $score1;
        $point_total{$winner2} += $score1;
        $point_total{$loser1} += $score2;
        $point_total{$loser2} += $score2;
        
	# Increment number of games for player
	$games{$winner1} +=1;
        $games{$winner2} +=1;
        $games{$loser1} +=1;
        $games{$loser2} +=1;

=pod
        @games{$winner1, $winner2, $loser1, $loser2} += (1,1,1,1);
        @wins{$winner1, $winner2} += (1,1);
        @losses{$loser1, $loser2} += (1,1);
        @point_total{$winner1, $winner2} += ($game_value,$game_value);
        @point_total{$loser1, $loser2}   -= ($game_value,$game_value);
=cut        
	# Get stats for a streak
        $streak{$winner1} = ($streak{$winner1}>0) 
		? $streak{$winner1} + 1 : 1;
	$streak{$winner2} = ($streak{$winner2}>0)
		? $streak{$winner2} + 1 : 1;
 	$streak{$loser1} = ($streak{$loser1}<0)
		? $streak{$loser1} - 1 : -1;
 	$streak{$loser2} = ($streak{$loser2}<0)
		? $streak{$loser2} - 1 : -1;

	$current_game++;
    }
    
    # Calculate winning percentage (average) and delta...
    foreach my $player (@players) {
    
        # Use instead for handicap... $delta{$player} = $point_total{$player};
	
	$delta{$player} = $wins{$player} - $losses{$player};
	
        $average{$player} = $games{$player} 
	    	? sprintf("%.0f", (($wins{$player} / $games{$player}) * 100)) 
		: '0';
    }
    
    # Put rank in order
    my $count_players = 1;
    foreach (sort { $delta{$b} <=> $delta{$a} } keys %delta) {
	$rank{$count_players} = $_;
        $count_players++;
    }
    
    return($number_of_games,$score1,$score2,$lastgame);
}

sub _ranking_sort {
    my $player_a = $rank{$a};
    my $player_b = $rank{$b};
    my $rank_a = $delta{$player_a} + $games;
    my $rank_b = $delta{$player_b} + $games;
	
    # Return sort conditionals
    $rank_b<=>$rank_a || 			 	 # Rank first
    $point_total{$player_b}<=>$point_total{$player_a} || # Then points
    $average{$player_b}<=>$average{$player_a} 		 # Then winning %
}

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Redirect to the web page if executed directly.
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
sub RedirectWebPage{
    my $url = shift || 'http://192.168.0.32/foosball.html';
    print "Location: $url\n\n";
}

#=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Output an Message to HTML
#=-=-=-=-=-=-=-=-=-=-=-=-=-=
sub OutputMsg{
    my $msg_text = shift;
    
    print header, $msg_text;
}

#=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Output an error to STDOUT
#=-=-=-=-=-=-=-=-=-=-=-=-=-=
sub OutputError{
    my $error_text = shift;
    
    print STDOUT "\n\n$error_text\n\n";
    exit;
}



#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#=-=-=-=	Begin HTML Output Templates
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=



# =-=-=-=-=-=-=-=-=-=
# CreateInputWebPage
# =-=-=-=-=-=-=-=-=-=
# Inputs: None.
# Outputs: Creates a web page for entering scores.
#
sub CreateInputWebPage {   
    # Text formatted to display the last game processed.
    my @data = ReadData($filename);
    my ($w1, $w2, $l1, $l2, $s1, $s2) = split (',',$data[$#data]);
    my $lastgame = "<b>$w1</b> and <b>$w2</b> ($s1) vs. <b>$l1</b> and <b>$l2</b> ($s2)";
   
    # Let's modify the global @players for our convenience here
    unshift @players, 'Choose:', '----------';
    
    my $tds = '<TD align=center width=150 BGCOLOR=';
    print header,
       start_html('Foosball Tournament Entry System'),
       '<CENTER>',h1('Foosball Tournament Entry System'),'<hr width=500>',
       start_form,"<u>Last game entered:</u> $lastgame<br>",
       '<TABLE border=0 cellspacing=10 cellpadding=3><TR><TD COLSPAN=2><b>Enter scores:</b>',
       '</TD></TR><TR>'.$tds.'"#AACCAA">Winner (offense)<br>',
       popup_menu(-name=>'winner1',
           -values=>\@players),p,
       '</TD>'.$tds.'"#AACCAA">Winner (defense)<br>',
       popup_menu(-name=>'winner2',
           -values=>\@players),p,
       '</TD>'.$tds.'"#AACCAA">Winning Score<br>',
       popup_menu(-name=>'score1',
           -values=>[1..20], -default=>8),p,
       '</TD></TR>'.$tds.'"#FFAAAA">Loser (offense)<br>',
       popup_menu(-name=>'loser1',
           -values=>\@players),p,
       '</TD>'.$tds.'"#FFAAAA">Loser (defense)<br>',
       popup_menu(-name=>'loser2',
           -values=>\@players),p,
       '</TD>'.$tds.'"#FFAAAA">Losing Score<br>',
       popup_menu(-name=>'score2',
           -values=>[1..20], -default=>4),p,
       '</TD></TR><TR><TD><TD>',
       submit,
       end_form,
       '</TD></TR></TABLE><br><br><i>Please allow several seconds for this script<br>',
       'to run as it has to generate the graph from scratch.<br><br></i>',
       'You will be redirected to the output page afterwards.';
   shift @players;
   shift @players;
}

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Output data to create a nicely formed WebPage
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Inputs (see below)
#
sub CreateWebPage{
    my $html 	 = shift;
    my $number_of_games = shift;
    my $score1 	 = shift;
    my $score2 	 = shift;
    my $lastgame = shift ||
    	OutputError('CreateWebPage called without correct parameters!');
    
    my @data = ();
    my @labels = ();
    my $dateprint = scalar localtime(time);

    # Begin html generation
    open (HTML, ">$html");
    print HTML <<"EOF";
<HTML>
<CENTER>
<h1><img src="images/flames.gif" height=50 valign=center>
&nbsp; &nbsp; Foosball &nbsp;<img src="images/crown.jpg" valign=center> &nbsp; Tournament &nbsp; &nbsp;
<img src="images/flames.gif" height=50 valign=top></h1>
Current as of $dateprint<br><br>
Last game entered: $lastgame<br><br>
<TABLE border=1 bordercolor=#000000 cellpadding=5 cellspacing=0 bgcolor=#000000 align=center>
<TR>
<TD width=30 align=center><font color=#FFFFFF><b>RANK</TD>
<TD width=100 align=center><font color=#FFFFFF><b>NAME</TD>
<TD width=30 align=center><font color=#FFFFFF><b>GAMES</TD>
<TD width=30 align=center><font color=#FFFFFF><b>WINS</TD>
<TD width=30 align=center><font color=#FFFFFF><b>LOSSES</TD>
<TD width=30 align=center><font color=#FFFFFF><b>RANKING SCORE</TD>
<TD width=30 align=center><font color=#FFFFFF bgcolor=#FFCCCC><b>STREAK</TD>
</TR>
EOF

    my $tdcolor = '#CCDDEE';
    my $last_rank = 0;
    my $ranking = 0;
    my $rank_html;
    
    foreach my $rank_order (sort _ranking_sort keys %rank) {
        my $player = $rank{$rank_order};
	my $tdc = "</TD><TD BGCOLOR=$tdcolor align=center>";
	my $tdl = "</TD><TD BGCOLOR=$tdcolor align=left>";
        my $new_rank = $delta{$player} + $number_of_games;
	    
	my $streaks = '</TD><TD BGCOLOR=';
	if ($streak{$player}>1) {    # Positive streak
	    $streaks .= "#CCFFCC align=center>+$streak{$player}";
	} 
	elsif ($streak{$player}<-1) { # Negative streak
	    $streaks .= "#FFCCCC align=center>$streak{$player}";
	} 
	elsif (!defined $streak{$player}) { # Hasn't played recently
	    $streaks .= "$tdcolor align=center>Absent";
	}
	else { # Nothing new, or break-even
	    $streaks .= "$tdcolor align=center>&nbsp;";
	}
	   
	# This will handle tie's
	if ($new_rank==$last_rank and $new_rank>1) {
	    $rank_html = "<TD BGCOLOR=$tdcolor align=center>&nbsp;";
	} else {
	    $ranking++;
	    $rank_html = "<TD BGCOLOR=#770088 align=center><font color=white><b>$ranking</b>";
	}
	# Now output the individual statistics
        print HTML "<TR>$rank_html$tdl$player$tdc$games{$player}$tdc$wins{$player}$tdc$losses{$player}$tdc$new_rank</TD>$streaks</TD></TR>\n";
        push @data, $average{$player} || .0000001;  # Graph can't handle a zero value.
        push @labels, "$player ($average{$player}%)";
        ($tdcolor eq '#CCDDEE') and $tdcolor='#FFFFFF' or $tdcolor='#CCDDEE';
	$last_rank = $new_rank;
    }
    print HTML "<TR rowspan=2><TD bgcolor=#FFFFFF colspan=7 align=center>*Note: In the case of a tie, the order is first sorted <br>by total points, then by winning percentages.</td></tr>\n";
    print HTML "</TABLE><br><a href=\"http://192.168.0.30/\">Return to Matador</a><br><br><img src=\"/images/foosball.jpg\"></CENTER>\n</HTML>";
    close HTML;

#=-=-=-=-=-=-=-=-=-=-=-=-=-=
#  Begin graph generation
#=-=-=-=-=-=-=-=-=-=-=-=-=-=
    ($ARGV[0]) and print "Data generated and updated.\nCreating graph...\n";

=pod
    use Imager;
    use Imager::Plot;
    
    #=-=-=-=-=-=-=-=-=-=
    # Begin bar graphs
    #=-=-=-=-=-=-=-=-=-=
    #
    my @X = [1..$games];
    my @Y = [$games..1];

    my $plot = Imager::Plot->new(Width  => 400,
                              Height => 300,
                              GlobalFont => 'ImUgly.ttf');
    $plot->AddDataSet(X  => \@X, Y => \@Y,
           style=>{marker=>{size   => 4,
                            symbol => 'circle',
                            color  => NC(0,120,0)
                           },
                   line=>{color=>NC(255,0,0)}
                  });
    my $img_bar = Imager->new(xsize=>600, ysize => 400);
    $img_bar->box(filled=>1, color=>Imager::Color->new(190,220,255));

    $plot->Render(Image => $imgpie, Xoff => 30, Yoff => 340);
    $img_bar->write(file => $jpgfile.'1');
=cut

    #=-=-=-=-=-=-=-=-=-=-=-=
    # Begin pie graphs...
    #=-=-=-=-=-=-=-=-=-=-=-=
    #
    my $textfont = Imager::Font->new(file=>'ImUgly.ttf')
      or die "Cannot create font object: ",Imager->errstr,"\n";
    
    my $pie = Imager::Graph::Pie->new;

    my $img_pie = $pie->draw(data=>\@data, labels=>\@labels,
                      font     => $textfont,
		      style    => 'fount_lin', 
                      features => [ 'labels' ],
		      size     => 320,
		      title    => 'Winning Percentages',
		     );

    ($ARGV[0]) and print "Saving graph...\n";
    $img_pie->write(file => $jpgfile);
    ($ARGV[0]) and print "Processing complete!\n";
}

# End of program!
