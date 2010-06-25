#!/usr/bin/perl 
#===============================================================================
#
#         FILE:  core.pl
#
#        USAGE:  ./core.pl  
#
#  DESCRIPTION:  Core for PoCo-IRC bot
#
#      OPTIONS:  ---
# REQUIREMENTS:  ---
#         BUGS:  ---
#        NOTES:  ---
#       AUTHOR:  Kyle Isom (coder@kyleisom.net)
#      COMPANY:  
#      VERSION:  1.0
#      CREATED:  06/25/2010 12:31:26 AM
#     REVISION:  ---
#===============================================================================

use strict;
use warnings;

use POE;
use POE::Component::IRC;
use POE::Component::IRC::State;
use POE::Component::IRC::Plugin::AutoJoin;

# variable declarations
my $nickname    =   "awesomeo4000";
my $username    =   "awesomeo4000";
my $server      =   "irc.freenode.net";
my @channels    =   ( "#awesomeotest" );

# create session and list event handlers
POE::Session -> create(
    package_states => [
        main => [ qw( _start _ircjoin ) ]
    ]
);

# start the session
$poe_kernel -> run();

# start IRC session
sub _start {
    my $irc = POE::Component::IRC::State->spawn(
        nick        => $nickname,
        username    => $username,
        server      => $server
    );

    $irc->plugin_add('AutoJoin', POE::Component::IRC::Plugin::AutoJoin->new(
        channels => @channels ));

    $irc->yield( join => $_ ) for @channels;
    $irc->yield( 'connect' );

    foreach (@channels) {
        my $ch = $_;
        $ch =~ s/^\#//;

        # you can send mad gr33tz from here
        
    }
}

sub _ircjoin {
    my $nick = (split /!/, $_[ARG0])[0];
    my $channel = $_[ARG1];
    my $irc = $_[SENDER]->get_heap();

    # only send the message if we were the one joining
    if ($nick eq $irc->$nickname) {
        $irc->yield(privmsg => $channel, 'hai devious');
    }
}

