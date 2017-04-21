# Enabled
%bcond_without compress
%bcond_without debug
%bcond_without gnutls
%bcond_without gpgme
%bcond_without gss
%bcond_without hcache
%bcond_without idn
%bcond_without imap
%bcond_without nntp
%bcond_without pop
%bcond_without sasl
%bcond_without sidebar
%bcond_without smtp
%bcond_without tokyocabinet

# Disabled
%bcond_with bdb
%bcond_with gdbm
%bcond_with kyotocabinet
%bcond_with qdbm

# Notmuch and lmdb don't exist on rhel, yet
%if 0%{?rhel}
# Disabled
%bcond_with notmuch
%bcond_with lmdb
%else
# Enabled
%bcond_without notmuch
%bcond_without lmdb
%endif

%global _origname mutt
%global _date 20170421

Summary: A text mode mail user agent
Name: neomutt
Version: 1.8.2
Release: %{_date}%{?dist}
Epoch: 5

%{!?_pkgdocdir: %global _pkgdocdir %{_docdir}/%{name}}

# The entire source code is GPLv2+ except
# pgpewrap.c setenv.c sha1.c wcwidth.c which are Public Domain
License: GPLv2+ and Public Domain
Group: Applications/Internet
# git snapshot created from https://github.com/neomutt/neomutt
Source: %{name}-%{_date}.tar.gz
Source1: mutt_ldap_query
Patch1: mutt-1.5.18-muttrc.patch
Patch2: mutt-1.5.21-cabundle.patch
Patch3: mutt-1.5.23-system_certs.patch
%if ! 0%{?rhel}
Patch4: mutt-1.5.23-ssl_ciphers.patch
%endif
Url: https://www.neomutt.org/
Requires: mailcap, urlview
Provides: %{_origname} = %{epoch}:%{version}
Obsoletes: %{_origname}
BuildRequires: ncurses-devel, gettext, automake, gettext-devel
# manual generation
BuildRequires: /usr/bin/xsltproc, docbook-style-xsl, perl
# html manual -> txt manual conversion (lynx messes up the encoding)
BuildRequires: w3m

%if %{with hcache}
%{?with_tokyocabinet:BuildRequires: tokyocabinet-devel}
%{?with_kyotocabinet:BuildRequires: kyotocabinet-devel}
%{?with_lmdb:BuildRequires: lmdb-devel}
%{?with_bdb:BuildRequires: libdb-devel}
%{?with_qdbm:BuildRequires: qdbm-devel}
%{?with_gdbm:BuildRequires: gdbm-devel}
%endif

%if %{with imap} || %{with pop} || %{with smtp}
%{?with_gnutls:BuildRequires: gnutls-devel}
%{?with_sasl:BuildRequires: cyrus-sasl-devel}
%endif

%if %{with imap}
%{?with_gss:BuildRequires: krb5-devel}
%endif

%{?with_idn:BuildRequires: libidn-devel}
%{?with_gpgme:BuildRequires: gpgme-devel}
%{?with_notmuch:BuildRequires: notmuch-devel}


%description
Mutt is a small but very powerful text-based MIME mail client.  Mutt
is highly configurable, and is well suited to the mail power user with
advanced features like key bindings, keyboard macros, mail threading,
regular expression searches and a powerful pattern matching language
for selecting groups of messages.


%prep
# unpack; cd
%setup -q -n %{name}-%{_date}
# disable mutt_dotlock program - disable post-install mutt_dotlock checking
sed -i -r 's|install-exec-hook|my-useless-label|' Makefile.am
%patch1 -p1 -b .muttrc
%patch2 -p1 -b .cabundle
%patch3 -p1 -b .system_certs
%if ! 0%{?rhel}
%patch4 -p1 -b .ssl_ciphers
%endif

autoreconf --install

sed -i -r 's/`$GPGME_CONFIG --libs`/"\0 -lgpg-error"/' configure
# disable mutt_dotlock program - remove support from mutt binary
sed -i -r 's|USE_DOTLOCK|DO_NOT_USE_DOTLOCK|' configure*

install -p -m644 %{SOURCE1} mutt_ldap_query

# Create a release date based on the rpm version
echo -n 'const char *ReleaseDate = ' > reldate.h
echo %{release} | sed -r 's/.*(201[0-9])([0-1][0-9])([0-3][0-9]).*/"\1-\2-\3";/' >> reldate.h

find . -type f -size 0 -name '*.neomutt' -delete

%build
%configure \
    SENDMAIL=%{_sbindir}/sendmail \
    ISPELL=%{_bindir}/hunspell \
    %{?with_debug:	--enable-debug}\
    %{?with_pop:	--enable-pop}\
    %{?with_imap:	--enable-imap} \
    %{?with_smtp:	--enable-smtp} \
    %{?with_sidebar:	--enable-sidebar} \
    %{?with_notmuch:	--enable-notmuch} \
    %{?with_nntp:	--enable-nntp} \
    %{?with_compress:	--enable-compressed} \
\
    %if %{with hcache}
    %{?with_tokyocabinet:	--with-tokyocabinet} \
    %{?with_kyotocabinet:	--with-kyotocabinet} \
    %{?with_lmdb:	--with-lmdb} \
    %{?with_gdbm:	--with-gdbm} \
    %{?with_qdbm:	--with-qdbm} \
    %{?with_bdb:	--with-bdb} \
    %endif
\
    %if %{with imap} || %{with pop} || %{with smtp}
    %{?with_gnutls:	--with-gnutls} \
    %{?with_sasl:	--with-sasl} \
    %endif
\
    %if %{with imap}
    %{?with_gss:	--with-gss} \
    %endif
\
    %{!?with_idn:	--without-idn} \
    %{?with_gpgme:	--enable-gpgme} \
    --with-docdir=%{_pkgdocdir}

make %{?_smp_mflags}

# remove unique id in manual.html because multilib conflicts
sed -i -r 's/<a id="id[a-z0-9]\+">/<a id="id">/g' doc/manual.html


%install
make install DESTDIR=$RPM_BUILD_ROOT

# we like GPG here
cat contrib/gpg.rc >> \
      $RPM_BUILD_ROOT%{_sysconfdir}/Muttrc

grep -5 "^color" contrib/sample.muttrc >> \
      $RPM_BUILD_ROOT%{_sysconfdir}/Muttrc

cat >> $RPM_BUILD_ROOT%{_sysconfdir}/Muttrc <<\EOF
source %{_sysconfdir}/Muttrc.local
EOF

echo "# Local configuration for Mutt." > \
      $RPM_BUILD_ROOT%{_sysconfdir}/Muttrc.local

# remove unpackaged files from the buildroot
rm -f $RPM_BUILD_ROOT%{_sysconfdir}/*.dist
rm -f $RPM_BUILD_ROOT%{_sysconfdir}/mime.types
# disable mutt_dotlock program - remove the compiled binary
rm -f $RPM_BUILD_ROOT%{_bindir}/mutt_dotlock
rm -f $RPM_BUILD_ROOT%{_bindir}/muttbug
rm -f $RPM_BUILD_ROOT%{_bindir}/flea
rm -f $RPM_BUILD_ROOT%{_mandir}/man1/mutt_dotlock.1*
rm -f $RPM_BUILD_ROOT%{_mandir}/man1/muttbug.1*
rm -f $RPM_BUILD_ROOT%{_mandir}/man1/flea.1*
rm -f $RPM_BUILD_ROOT%{_mandir}/man5/mbox.5*
rm -f $RPM_BUILD_ROOT%{_mandir}/man5/mmdf.5*

rm -rf $RPM_BUILD_ROOT%{_pkgdocdir}/samples
rm -rf $RPM_BUILD_ROOT%{_pkgdocdir}/applying-patches.txt
rm -rf $RPM_BUILD_ROOT%{_pkgdocdir}/devel-notes.txt
rm -rf $RPM_BUILD_ROOT%{_pkgdocdir}/INSTALL
rm -rf $RPM_BUILD_ROOT%{_pkgdocdir}/patch-notes.txt
rm -rf $RPM_BUILD_ROOT%{_pkgdocdir}/PGP-Notes.txt
rm -rf $RPM_BUILD_ROOT%{_pkgdocdir}/TODO

%if 0%{?rhel}
rm -rf $RPM_BUILD_ROOT%{_docdir}/neomutt
%endif

# provide muttrc.local(5): the same as muttrc(5)
ln -sf ./muttrc.5 $RPM_BUILD_ROOT%{_mandir}/man5/muttrc.local.5

%find_lang %{_origname}

%files -f %{_origname}.lang
%config(noreplace) %{_sysconfdir}/Muttrc
%config(noreplace) %{_sysconfdir}/Muttrc.local
%doc COPYRIGHT ChangeLog* LICENSE.md NEWS README* UPDATING mutt_ldap_query
%doc contrib/*.rc contrib/sample.* contrib/colors.*
%doc doc/muttrc.* doc/neomutt-syntax.vim
%doc doc/manual.txt doc/smime-notes.txt
%doc doc/*.html
%doc contrib/keybase
%doc contrib/vim-keys
%{_bindir}/mutt
%{_bindir}/pgpring
%{_bindir}/pgpewrap
%{_bindir}/smime_keys
%{_mandir}/man1/mutt.*
%{_mandir}/man1/smime_keys.*
%{_mandir}/man1/pgpring.*
%{_mandir}/man1/pgpewrap.*
%{_mandir}/man5/muttrc.*

%changelog
* Mon Apr 21 2017 Richard Russon <rich@flatcap.org> - NeoMutt-20170421
- Features
  - add lua scripting
  - add command-line batch mode
  - index_format: add support of %K
- Bug Fixes
  - attachment/pager: Use mailcap for test/* except plain
  - Fix uncollapse_new in pager
  - fix garbage in chdir prompt due to unescaped string
  - Fix inbox-first functionality when using mutt_pretty_mailbox
  - add full neomutt version to log startup
  - fix bug in uncolor for notmuch tag
  - fix broken from_chars behaviour
- Coverity defects
  - strfcpy
  - add variable - function arg could be NULL/invalid
  - add variable - failed function leads to invalid variable
  - add variable - Context could become NULL
  - add variable - alloc/strdup could return NULL
  - add variable - route through code leads to invalid variable
  - remove variable test
  - test functions
  - tidy switches
  - unused variables
  - refactor only
  - check for buffer underruns
  - fix leaks
  - minor fixes
  - bug: add missing break
  - bug: don't pass large object by value
  - fix: use correct buffer size
  - shadow variables
  - 0 -> NULL
- Docs
  - many minor updates
  - sync translations
  - delete trailing whitespace
  - indent the docbook manual
  - use w3m as default for generating UTF8 manual.txt
- Website
  - many minor updates
  - fix broken links
  - add to list of useful programs
  - test automatic html checker
  - remove trailing whitespace
  - add irc description
  - update issue labels (dev)
  - new page: closed discussions
  - new page: making neomutt (dev)
- Build
  - drop obsolete m4 scripts
  - don't look for lua libs unless asked for
  - workaround slang warnings
  - lower the gettext requirement 0.18 -> 0.17
  - add keymap_alldefs.h to BUILT_SOURCES
  - fix make dist distcheck
  - Remove -Iimap from CFLAGS and include imap/imap.h explicitly
  - mx: fix conditional builds
  - Make iconv mandatory (no more --disable-iconv)
  - refactor: Split out BUFFER-handling functions
- Tidy
  - drop control characters from the source
  - drop vim modelines
  - delete trailing whitespace
  - mark all local functions as static
  - delete unused functions
  - replace FOREVER with while (true)
  - drop #if HAVE_CONFIG_H
  - use #ifdef for potentially missing symbols
  - remove #if 0 code blocks
  - drop commented out source
  - IMAP auth functions are stored by pointer cannot be static
  - force OPS to be rebuilt after a reconfigure
  - be specific about void functions
  - expand a few more alloc macros
  - add argument names to function prototypes
  - drop local copy of regex code
  - rearrange code to avoid forward declarations
  - limit the scope of some functions
  - give the compress functions a unique name
  - use snake_case for function names
  - add missing newlines to mutt_debug
  - remove generated files from repo
  - look for translations in all files
  - fix arguments to printf-style functions
  - license text
  - unify include-guards
  - tidy makefiles
  - initialise pointers
  - make strcmp-like functions clearer
  - unify sizeof usage
  - remove forward declarations
  - remove ()s from return
  - rename files hyphen to underscore
  - remove unused macros
  - use SEEK_SET, SEEK_CUR, SEEK_END
  - remove constant code
  - fix typos and grammar in the comments
  - Switch to using an external gettext runtime
  - apply clang-format to the source code
  - boolify returns of 84 functions
  - boolify lots of struct members
  - boolify some function parameters
- Upstream
  - Add $ssl_verify_partial_chains option for OpenSSL
  - Move the OpenSSL partial chain support check inside configure.ac
  - Don't allow storing duplicate certs for OpenSSL interactive prompt
  - Prevent skipped certs from showing a second time
  - OpenSSL: Don't offer (a)ccept always choice for hostname mismatches
  - Add SNI support for OpenSSL
  - Add SNI support for GnuTLS
  - Add shortcuts for IMAP and POP mailboxes in the file browser
  - Change OpenSSL to use SHA-256 for cert comparison
  - Fix conststrings type mismatches
  - Pass envlist to filter children too
  - Fix mutt_envlist_set() for the case that envlist is null
  - Fix setenv overwriting to not truncate the envlist
  - Fix (un)sidebar_whitelist to expand paths
  - Fix mutt_refresh() pausing during macro events
  - Add a menu stack to track current and past menus
  - Change CurrentMenu to be controlled by the menu stack
  - Set refresh when popping the menu stack
  - Remove redraw parameter from crypt send_menus
  - Don't full redraw the index when handling a command from the pager
  - Filter other directional markers that corrupt the screen
  - Remove the OPTFORCEREDRAW options
  - Remove SidebarNeedsRedraw
  - Change reflow_windows() to set full redraw
  - Create R_MENU redraw option
  - Remove refresh parameter from mutt_enter_fname()
  - Remove redraw flag setting after mutt_endwin()
  - Change km_dokey() to pass SigWinch on for the MENU_EDITOR
  - Separate out the compose menu redrawing
  - Separate out the index menu redrawing
  - Prepare for pager redraw separation
  - Separate out the pager menu redrawing
  - Don't create query menu until after initial prompt
  - Silence imap progress messages for pipe-message
  - Ensure mutt stays in endwin during calls to pipe_msg()
  - Fix memleak when attaching files
  - Add $ssl_verify_partial_chains option for OpenSSL
  - Move the OpenSSL partial chain support check inside configureac
  - Don't allow storing duplicate certs for OpenSSL interactive prompt
  - Prevent skipped certs from showing a second time
  - OpenSSL: Don't offer (a)ccept always choice for hostname mismatches
  - Add SNI support for OpenSSL
  - Add SNI support for GnuTLS
  - Add shortcuts for IMAP and POP mailboxes in the file browser
  - Updated French translation
  - Change OpenSSL to use SHA-256 for cert comparison
  - Fix conststrings type mismatches
  - Pass envlist to filter children too
  - Fix mutt_envlist_set() for the case that envlist is null
  - Fix setenv overwriting to not truncate the envlist
  - Fix mutt_refresh() pausing during macro events
  - Add a menu stack to track current and past menus
  - Change CurrentMenu to be controlled by the menu stack
  - Set refresh when popping the menu stack
  - Remove redraw parameter from crypt send_menus
  - Don't full redraw the index when handling a command from the pager
  - Fix (un)sidebar_whitelist to expand paths
  - Filter other directional markers that corrupt the screen
  - Remove the OPTFORCEREDRAW options
  - Remove SidebarNeedsRedraw
  - Change reflow_windows() to set full redraw
  - Create R_MENU redraw option
  - Remove refresh parameter from mutt_enter_fname()
  - Remove redraw flag setting after mutt_endwin()
  - Change km_dokey() to pass SigWinch on for the MENU_EDITOR
  - Separate out the compose menu redrawing
  - Separate out the index menu redrawing
  - Prepare for pager redraw separation
  - Separate out the pager menu redrawing
  - Don't create query menu until after initial prompt
  - Silence imap progress messages for pipe-message
  - Ensure mutt stays in endwin during calls to pipe_msg()
  - Fix memleak when attaching files
  - automatic post-release commit for mutt-181
  - Added tag mutt-1-8-1-rel for changeset f44974c10990
  - mutt-181 signed
  - Add ifdefs around new mutt_resize_screen calls
  - Add multiline and sigwinch handling to mutt_multi_choice
  - Set pager's REDRAW_SIGWINCH when reflowing windows
  - Add multiline and sigwinch handling to mutt_yesorno
  - Change the sort prompt to use (s)ort style prompts
  - Handle the pager sort prompt inside the pager
  - Fix GPG_TTY to be added to envlist
  - automatic post-release commit for mutt-182

* Fri Apr 14 2017 Richard Russon <rich@flatcap.org> - NeoMutt-20170414
- Devel Release

* Mon Mar 06 2017 Richard Russon <rich@flatcap.org> - NeoMutt-20170306
- Bug Fixes
  - Get the correct buffer size under fmemopen/torify (#441)
  - Use static inlines to make gcc 4.2.1 happy
  - getdnsdomainname: cancel getaddrinfo_a if needed
  - imap: remove useless code (#434) (origin/master)
  - Fixes missing semi-colon compilation issue (#433)
- Docs
  - github: added template for Pull Requests, issues and a CONTRIBUTION.md (#339)
  - editorconfig: support for new files, fix whitespace (#439)
  - add blocking fmemopen bug on debian to manual (#422)
- Upstream
  - Increase ACCOUNT.pass field size. (closes #3921)
  - SSL: Fix memory leak in subject alternative name code. (closes #3920)
  - Prevent segv if open-appending to an mbox fails. (closes #3918)
  - Clear out extraneous errors before SSL_connect() (see #3916)

* Sat Feb 25 2017 Richard Russon <rich@flatcap.org> - NeoMutt-20170225
- Features
  - Add option $show_multipart_alternative
  - notmuch: Allow to use untransformed tag for color
  - Use getaddrinfo_a if possible (#420)
- Bug Fixes
  - handle sigint within socket operations (#411)
  - Avoid browsing the remote spoolfile by setting MUTT_SELECT_MULTI attach
  - notmuch: fix crash when completing tags (#395)
  - Fixes missing failure return of notmuch msg open (#401)
  - Fix latest Coverity issues (#387)
  - Advance by the correct number of position even for unknown characters (#368)
  - Release KyotoCabinet data with kcfree() (#384)
  - 22 resource leaks
- Translations
  - Update translations
  - Update the german translation (#397)
- Docs
  - fix typo in notmuch example
  - remove duplicate "default" in the sidebar intro
  - fix confusing description of notmuch operators (#371)
  - correct spelling mistakes (#412)
- Website
  - link to clang-format config in main repo (#28)
  - updated list of useful programs
  - update/improve list of useful programs
  - sidebar_format has a single default value
  - fix name of GNU Guix
  - added guix distro
  - added link to new afew maintainers
  - add code of conduct
  - add mutt-addressbook to useful
  - remove unnecessary unicode non-breaking spaces
  - github merging
- Build
  - Enable and run unit-tests on the feature/unit-test branch
  - add notmuch to default, feature
  - new dbs for mutt
  - master is now the main branch
  - streamline builds
  - fix doc generator
  - add a few includes (prelude to clang-format)
  - slcurses.h defines its own bool type
  - travis: use container build
  - add clang-format file
  - Remove ugly macros and casts from crypt-gpgme.c
  - fix minor reflow issues in some comments
  - editorconfig: use spaces to indent in *.[ch] files
  - added comment-blocks for clang-format to ignore
  - fix 80 column limit, align statements
  - Remove snprintf.c from EXTRA_DIST (#406)
  - Kill homebrew (v)snprintf implementations, as they are C99 (#402)
  - Display charset + small refactoring
  - Do not cast or check returns from safe_calloc (#396)
  - refactor: create a generic base64 encode/decode
  - debug: remove dprint in favor of mutt_debug (#375)
  - Fix dubious use macro for _() / gettext() (#376)
  - Use mutt_buffer_init instead of memset
  - Make the heap method and datatype a plain list
  - Reverts making AliasFile into a list_t (#379)
  - Turn mutt_new_* macros into inline functions
  - Do not cast return values from malloc (et similia)
- Upstream
  - Simplify mutt_label_complete().
  - Permit tab completion of pattern expressions with ~y (labels).
  - Fix the mutt_label_complete() pos parameter.
  - Fix the x-label update code check location.
  - Improve the label completion hash table usage.
  - Adds label completion.
  - Add hash_find_elem to get the hash element.
  - Minor fixes to the x-label patch from David.
  - Adds capability to edit x-labels inside mutt, and to sort by label.
  - Allow "unsubjectrc *" to remove all patterns.
  - Add subjectrx command to replace matching subjects with something else.
  - Abstract the SPAM_LIST as a generic REPLACE_LIST
  - Improve Reply-to vs From comparison when replying. (closes #3909)
  - Fix sidebar references to the "new count" to be "unread". (closes #3908)
  - Fix several alias hashtable issues.
  - Add casecmp and strdup_key flags to hash_create()
  - Improve error handling in mbox magic detection.
  - Allow initial blank lines in local mailboxes.
  - Fix minor documentation issues.
  - Convert cmd_parse_search to use the uid hash. (closes #3905)
  - Create a uid hash for imap. (see #3905)
  - Convert HASH to be indexable by unsigned int. (see #3905)
  - Fix imap server-side search to call uid2msgno() only once. (see #3905)
  - Add a pattern_cache_t to speed up a few repeated matches.
  - Canonicalize line endings for GPGME S/MIME encryption. (closes #3904)
  - Fix build for bdb.
  - Create function to free header cache data.
  - Add Kyoto Cabinet support to the header cache.
  - Prevent null pointer exception for h->ai_canonname
  - Show SHA1 fp in interactive cert check menu.
  - Fix potential cert memory leak in check_certificate_by_digest().
  - Plug memory leak in weed-expired-certs code.
  - Filter expired local certs for OpenSSL verification.
  - Change "allow_dups" into a flag at hash creation.

* Mon Feb 06 2017 Richard Russon <rich@flatcap.org> - NeoMutt-20170206
- Bug Fixes
  - Unicode 0x202F is a non-break space too (#358)
  - improve readability of find_subject()
  - Import hcache-lmdb fixes from upstream (#363)
  - Rework the "inbox-first" implementation to make code self-explanatory (#356)
  - If possible, only redraw after gpgme has invoked pinentry (#352)
  - Remove two use-after free in global hooks (#353)
  - Handle BAD as IMAP_AUTH_UNAVAIL (#351)
  - Do not crash when closing a non-opened mailbox (origin/requests/github/343)
  - Import hcache benchmark
  - fix: bug introduced by mkdir changes (#350)
  - change pager to allow timehook-hook to fire
- Docs
  - Update documentation about modify-labels-then-hide

* Sat Jan 28 2017 Richard Russon <rich@flatcap.org> - NeoMutt-20170128
- Features
  - Add option for missing subject replacement
  - notmuch: Allow <modify-labels> to toggle labels
  - Support for aborting mailbox loading
  - Do a buffy check after shell escape
  - Support of relative paths sourcing and cyclic source detection
  - Support of multiple config files as CLI arguments
  - Extend the ~m pattern to allow relative ranges
  - Implement SASL's PLAIN mechanism as a standalone authenticator
  - Add support for sensitive config options
  - Searching with a window over notmuch vfolders
- Contrib
  - fix vim syntax file for index-color commands
  - add .editorconfig
- Bug Fixes
  - fix global hooks to not take a pattern
  - Avoid breaking relative paths when avoiding cyclic checks on
  - Fix sorting when using '/' as a namespace separator
- Docs
  - Added waffle badges to readme
  - Describe the new message ranges
  - add documentation for -DS command line switch
  - fix typos in section on config locations
  - remove reference to missing keybinding
  - fix docbook validation
- Build
  - Start migrating to stdbool logic
  - add recursive mkdir()
  - reformat the source to mutt standards
  - appease check_sec.sh

* Fri Jan 13 2017 Richard Russon <rich@flatcap.org> - NeoMutt-20170113
- Features
  - Allow custom status flags in index_format
  - $from_chars highlights differences in authorship
  - notmuch: make 'Folder' and 'Tags' respect (un)ignore
  - notmuch: add "virtual-unmailboxes" command
- Bug Fixes
  - pick smarter default for $sidebar_divider_char
  - status color breaks "mutt -D"
  - Enable reconstruct-thread in the pager
  - manually touch 'atime' when reading a mbox file
  - allow $to_chars to contain Unicode characters
  - increase the max lmdb database size
  - restore limit current thread
  - don't reset the alarm unless we set it
  - some more places that may get NULL pointers
  - rework initials to allow unicode characters
- Translations
  - Spanish translation
  - German translation
- Docs
  - Improve whitespace and grammar on the NNTP feature page
  - make $to_chars docs more legible
  - de-tab the DocBook
  - fix 301 redirects
- Build
  - New configure option --enable-everything
  - add a constant for an aborted question
  - enhance mutt_to_base64() (and callers)
  - Fix configure.ac to require md5 if hcache is enabled
  - Bail if a selected hcache backend cannot be found
  - refactor mutt_matches_ignore
  - fix hcache + make dist
  - add unicode string helper function
  - Re-indent configure.ac
  - generate devel version suffix
  - fix check_sec.sh warnings
  - remove unnecessary #ifdef's
  - add missing #ifdef for nntp
  - ignore some configure temp files
  - fix "make dist" target
  - fix function prototypes
  - fix coverity warnings
  - notmuch: drop strndup, replace with mutt_substrdup
- Upstream
  - Fix failure with GPGME 1.8: do not steal the gpgme_ prefix.
  - search muttrc file according to XDG Base Specification (closes #3207)
  - Improve openssl interactive_check_cert. (closes #3899)
  - Add mutt_array_size macro, change interactive_check_cert() to use it. (see #3899)
  - Return to pager upon aborting a jump operation. (closes #3901)
  - Change sidebar_spoolfile coloring to be lower precedence.
  - Move '@' pattern modifier documentation to the right section.
  - Add setenv/unsetenv commands.
  - Rework OpenSSL certificate verification to support alternative chains. (closes #3903)
  - Add option to control whether threads uncollapse when new mail arrives.
  - In the manual, replaced 2 para by example (similar to the first example).
  - Create mbchar_table type for multibyte character arrays. (see #3024)
  - Make to_chars and status_chars accept mulitibyte characters. (closes #3024)

* Sat Nov 26 2016 Richard Russon <rich@flatcap.org> - NeoMutt-20161126
- Features
  - Upstream adoption of compress
  - Multiple hcache backends and run-time selection
  - $forward_references includes References: header on forwards
  - Hooks: define hooks for startup and shutdown
  - Add $collapse_all to close threads automatically
- Bug Fixes
  - Index in pager crash
  - Tag with multiple labels
  - Make sure gdbm's symbols are not resolved in QDBM's compatibility layer
  - Fix crash when doing collapse_all on an empty folder
  - Fix: crash when browsing empty dir
  - Initialize imap_authenticate's return value to something meaningful
- Translations
  - Update German translation
  - Update Slovak translation
  - Update French translation
  - Add English (British) translation
  - Convert files to utf-8
  - Mass tidy up of the translation messages
- Docs
  - new-mail bug is fixed
  - add since date for features
  - expand example command options for compress
  - fix entries for beep and new-mail-command
  - add a version number to the generated vimrc
  - fix links in README
  - don't use smart quotes in manual examples
  - <escape> and \e means refers to both alt and escape key
- Build
  - Travis: test messages
  - Add option to disable translation messages
  - Split hcache code into per-backend files
  - Doc/Makefile clean neomutt-syntax.vim
  - Improve discovery for the Berkeley Database
  - Fix nntp/notmuch conditionals
  - Implement mutt_strchrnul()
  - Rename vim-keybindings to vim-keys
- Upstream
  - attach_format: add new %F placeholder
  - Compose: add operation to rename an attachment
  - Chain %d->%F->%f in the attachment menu
  - Move mbox close-append logic inside mbox_close_mailbox()
  - When $flag_safe is set, flagged messages cannot be deleted
  - Adds the '@' pattern modifier to limit matches to known aliases
  - Adds <mark-message> binding to create "hotkeys" for messages
  - Updated requirement on the C compiler
  - Fix mark-message translation and keybind menu
  - More openssl1.1 fixes: remove uses of X509->name in debugging. (closes #3870)
  - Don't close stderr when opening a tunnel. (closes #3726)
  - Minor resource and error logic cleanup in tunnel_socket_open()
  - Make sure that the output of X509_NAME_oneline is null-terminated

* Fri Nov 04 2016 Richard Russon <rich@flatcap.org> - NeoMutt-20161104
- Bug Fixes
  - don't crash when the imap connection dies
- Upstream
  - Add root-message function to jump to root message in thread.
  - Updated French translation.
  - Prevent an integer overflow in mutt_mktime() (closes #3880)
  - Fix pager segfault when lineInfo.chunks overflows. (closes #3888)
  - Perform charset conversion on text attachments when piping. (closes #3773) (see #3886)
  - Add a --disable-doc configuration option.
  - Make ncurses and ncursesw header checking the same.
  - Attempt to silence a clang range warning. (closes #3891)
  - Fixed issue from changeset 4da647a80c55. (closes #3892)
  - Define PATH_MAX, it's missing on the GNU Hurd. (closes #3815)

* Fri Oct 28 2016 Richard Russon <rich@flatcap.org> - NeoMutt-20161028
- Features
  - nntp: use safe_{fopen,fclose}
  - nntp: fix resource leak
  - forgotten-attachment: Ignore lines matching quote_regexp.
  - forgotten-attachment: Fix checking logic.
  - forgotten-attachment: Update docs regarding $quote_regexp.
  - notmuch: Add a fake "Folder" header to viewed emails
  - sidebar: consider description when using whitelist
  - skip-quoted: skip to body
- Bug Fixes
  - sensible-browser/notmuch changing mailbox
  - "inbox" sorting function
  - overhaul the index/pager updates
  - crash in hdrline
  - remove stray line introduced by pager fix
  - Possible fix for random pager crashes.
- Docs
  - use a more expressive coverity scan badge
  - light tidying
- Build
  - replace the ugly strfcpy() macro with a function
  - build: Look for tgetent in ncurses, fallback to tinfo only if not found
  - build: fix a couple of build warnings
  - travis: install doc dependencies
  - build: fix install/dist/distcheck targets
- Upstream
  - Fix POP3 SASL authentication mechanism DIGEST-MD5. (closes #3862)
  - Add a few explanatory comments to pop_auth_sasl().  (see #3862)
  - Fix GPGME signature zero timestamp and locale awareness issues. (closes #3882)
  - Handle presence of '--' delimiter in $sendmail. (closes #3168)
  - Allow IPv6 literal addresses in URLs. (closes #3681)
  - Fix gpgme segfault in create_recipient_set().
  - Use mutt_strlen and mutt_strncmp in sidebar.c.
  - Change sidebar to only match $folder prefix on a $sidebar_divider_char. (closes #3887)
  - Actually fix gpgme segfault in create_recipient_set().

* Fri Oct 14 2016 Richard Russon <rich@flatcap.org> - NeoMutt-20161014
- Features
  - sidebar: Make sure INBOX appears first in the list.
  - notmuch: Synchronise tags to flags
- Bug Fixes
  - updates when pager is open
  - crash when neither $spoolfile, $folder are set
  - forgotten-attachment: fix empty regex expression
  - status-color when pager_index_lines > 0
  - buffer underrun when no menu item is selected
  - crash handling keywords/labels
- Docs
  - update notmuch references
- Build
  - update references to 1.7.1
  - strfcpy() improvement
- Upstream
  - automatic post-release commit for mutt-1.7.1
  - Mark IMAP fast-trash'ed messages as read before copying. (see #3860)
  - Updated Czech translation.
  - Preserve forwarded attachment names in d_filename.

* Mon Oct 03 2016 Richard Russon <rich@flatcap.org> - NeoMutt-20161003
- Build
  - Fix install and dist targets

* Sun Oct 02 2016 Richard Russon <rich@flatcap.org> - NeoMutt-20161002
- Features
  - Kyoto Cabinet header cache
  - Compose to Sender
  - Forgotten Attachment uses a regex
  - Optimize LMDB's hcache backend
  - Sensible-browser behaviour fixes
- Bug Fixes
  - Fixes repaint problem with $pager_index_lines #159
  - Quasi-Delete: check there's a selection
  - Bulletproof the pager
  - Typo in the version string
- Docs
  - Add badges to README.neomutt
  - Document the Kyoto cabinet hcache backend
  - Fix the layout of the syntax file
  - Make the license clear to github
  - Fix the alignment in a 'nested-if' example
  - Fix notmuch vim syntax file
  - Added Mailinglist mailto links to "Where is NeoMutt" section
  - Fix build of neomutt-syntax.vim
  - Fixed typo of devel mailinglist name
- Build
  - Travis: install the kyoto-cabinet dev files
  - Build source before docs
  - Build fix for strndup / malloc
  - Change gcc build options to prevent crashes
- Upstream
  - Ensure signatures exist when verifying multipart/signed emails. (closes #3881).
  - RFC2047-decode mailto url headers after RFC2822 parsing. (closes #3879)
  - RFC2047-decode mailto header values. (closes #3879)
  - Reset invalid parsed received dates to 0.  (closes #3878)
  - Clear pager position when toggling headers.
  - Don't abort the menu editor on sigwinch. (closes #3875)
  - Mark some gpgme pgp menu keybinding translations as fuzzy. (closes #3874)
  - Check for NULL mx_ops in mx.c
  - Use body color for gpgme output. (closes #3872)
  - Fix gpgme segfault when querying candidates with a '+' in the address. (closes #3873)

* Fri Sep 16 2016 Richard Russon <rich@flatcap.org> - NeoMutt-20160916
- Bug Fixes
  - Avoid segfault when listing mailboxes on startup
    John Swinbank
  - Fix buffer overrun in search for attach keyword
    James McCoy
  - Fix off-by-one in error message
    Antonio Radici
  - fix AC_INIT tarname parameter
  - fix crash when exiting the pager
  - fix another crash in the pager
  - nntp: close message handles
  - fix: make the pager more robust
  - fix sidebar sort order
  - fix notmuch tag completion
- Docs
  - doc: Removes bug entry in new-mail docs
    Santiago Torres
  - fix some translations in crypt-gpgme.c
    Antonio Radici
  - docs: mass tidy up
- Upstream
  - Fix sidebar documentation a bit
  - Add unsidebar_whitelist command
  - Remove the $locale configuration variable
  - Add $attribution_locale configuration variable
  - Add missing include <locale.h> to send.c and edit.c
  - Filter out zero width no-break space (U+FEFF)
  - Update a confusing and obsolete comment
  - Moves mutt_copy_list to muttlib.c, where it belongs
  - Redraw screen after an SSL cert prompt
  - Preserve message-id and mft headers for recalled messages
  - Fix openssl 1.1 compilation issues

* Sat Sep 10 2016 Richard Russon <rich@flatcap.org> - NeoMutt-20160910
- New Features
  - Colouring Attachments with Regexp
    Guillaume Brogi (guiniol)
  - PGP Encrypt to Self
    Guillaume Brogi (guiniol)
  - Sensible Browser
    Pierre-Elliott Bécue (p-eb)
  - Reply using X-Original-To: header
    Pierre-Elliott Bécue (p-eb)
  - Purge Thread
    Darshit Shah (darnir)
  - Forgotten attachment
    Darshit Shah (darnir)
  - Add sidebar_ordinary color
- Bug Fixes
  - align the nntp code with mutt
    Fabian Groffen (grobian)
  - check for new mail while in pager when idle
    Stefan Assmann (sassmann)
  - Allow the user to interrupt slow IO operations
    Antonio Radici (aradici)
  - keywords: check there are emails to tag
  - fix duplicate saved messages
  - flatten contrib/keybase dir to fix install
  - restore the pager keymapping 'i' to exit
  - proposed fix for clearing labels
  - notmuch: sync vfolder_format to folder_format
- Docs
  - Update List of Features and Authors
- Build
  - fix configure check for fmemopen
  - use fixed version strings
- Upstream
  - Increase date buffer size for $folder_format.
  - Disable ~X when message scoring.
  - Fix pgpring reporting of DSA and Elgamal key lengths.
  - Stub out getdnsdomainname() unless HAVE_GETADDRINFO.
  - Autoconf: always check for getaddrinfo().
  - Add missing sidebar contrib sample files to dist tarball.

* Sat Aug 27 2016 Richard Russon <rich@flatcap.org> - NeoMutt-20160827
- Ported to Mutt-1.7.0

* Fri Aug 26 2016 Richard Russon <rich@flatcap.org> - NeoMutt-20160826
- Build
  - Disable fmemopen until bug is fixed
- Contrib
  - Keybase portability improvements
    Joshua Jordi (JakkinStewart)
- Bug Fixes
  - Fix notmuch crash toggling virtual folders 
  - Fix display of pager index when sidebar toggled

* Sun Aug 21 2016 Richard Russon <rich@flatcap.org> - NeoMutt-20160821
- Contrib
  - Updates to Keybase Support
    Joshua Jordi (JakkinStewart)
- Bug Fixes
  - Fix data-loss when appending a compressed file
  - Don't paint invisible progress bars
  - Revert to Mutt keybindings
  - Don't de-tag emails after labelling them
  - Don't whine if getrandom() fails
    Adam Borowski (kilobyte)
  - Fix display when 'from' field is invalid
- Config
  - Support for $XDG_CONFIG_HOME and $XDG_CONFIG_DIRS
    Marco Hinz (mhinz)
- Docs
  - Fix DocBook validation
  - Document NotMuch queries
- Build
  - More Autoconf improvements
    Darshit Shah (darnir)
  - Create Distribution Tarballs with autogen sources
    Darshit Shah (darnir)

* Mon Aug 08 2016 Richard Russon <rich@flatcap.org> - NeoMutt-20160808
- New Features
  - Timeout Hook - Run a command periodically
  - Multiple fcc - Save multiple copies of outgoing mail
- Contrib
  - Keybase Integration
    Joshua Jordi (JakkinStewart)
- Devel
  - Attached - Prevent missing attachments
    Darshit Shah (darnir)
  - Virtual Unmailboxes - Remove unwanted virtual mailboxes
    Richard Russon (flatcap)
- Bug Fixes
  - Sidebar's inbox occasionally shows zero/wrong value
  - Fix crash opening a second compressed mailbox
- Config
  - Look for /etc/NeoMuttrc and ~/.neomuttrc
- Docs
  - Fix broken links, typos
  - Update project link
  - Fix version string in the manual
- Build
  - Add option to disable fmemopen
  - Install all the READMEs and contribs
  - Big overhaul of the build
    Darshit Shah (darnir)

* Sat Jul 23 2016 Richard Russon <rich@flatcap.org> - NeoMutt-20160723
- New Motto: "Teaching an Old Dog New Tricks"
  - Thanks to Alok Singh
- New Features
  - New Mail Command - Execute a command on receipt of new mail
  - vim-keybindings - Mutt config for vim users
  - LMDB: In-memory header caching database
  - SMIME Encrypt to Self - Secure storage of sensitive email
- Bug Fixes
  - rework mutt_draw_statusline()
  - fix cursor position after sidebar redraw
  - Add sidebar_format flag '%n' to display 'N' on new mail.
  - fix index_format truncation problem
  - Fix compiler warnings due to always true condition
  - Change sidebar next/prev-new to look at buffy->new too.
  - Change the default for sidebar_format to use %n.
  - sidebar "unsorted" order to match Buffy list order.
  - Include ncurses tinfo library if found.
  - Sidebar width problem
  - sidebar crash for non-existent mailbox
  - Temporary compatibility workaround
  - Reset buffy->new for the current mailbox in IMAP.
  - version.sh regression
  - crash when notmuch tries to read a message
  - status line wrapping
- Docs
  - Mass tidy up of the docs
  - Fix xml validation
  - Add missing docs for new features
- Travis
  - New build system:
    https://github.com/neomutt/travis-build
    Now we have central control over what gets built

* Sat Jul 09 2016 Richard Russon <rich@flatcap.org> - NeoMutt-20160709
- Bug-fixes
  - This release was a temporary measure

* Sat Jun 11 2016 Richard Russon <rich@flatcap.org> - NeoMutt-20160611
- Change in behaviour
  - Temporarily disable $sidebar_refresh_time
    Unfortunately, this was causing too many problems.
    It will be fixed and re-enabled as soon as possible.
- Bug Fixes
  - Fix several crashes, on startup, in Keywords
  - Reflow text now works as it should
  - Lots of typos fixed
  - Compress config bug prevented it working
  - Some minor bug-fixes from mutt/default
  - Single quote at line beginning misinterpreted by groff
  - Setting $sidebar_width to more than 128 would cause bad things to happen.
  - Fix alignment in the compose menu.
  - Fix sidebar buffy stats updating on mailbox close.
- Build Changes
  - Sync whitespace to mutt/default
  - Alter ChangeLog date format to simplify Makefiles
  - Use the new notmuch functions that return a status
  - Rename sidebar functions sb_* -> mutt_sb_*

* Mon May 23 2016 Richard Russon <rich@flatcap.org> - NeoMutt-20160523
- New Features:
  - Keywords: Email Label/Keywords/Tagging
  - Compress: Compressed mailboxes support
  - NNTP: Talk to a usenet news server
  - Separate mappings for <enter> and <return>
  - New configure option: --enable-quick-build
  - Various build fixes

* Mon May 02 2016 Richard Russon <rich@flatcap.org> - NeoMutt-20160502
- Update for Mutt-1.6.0
- Bug Fixes:
  - Build for Notmuch works if Sidebar is disabled
  - Sidebar functions work even if the Sidebar is hidden
  - sidebar-next-new, etc, only find *new* mail, as documented
  - Notmuch supports *very* long queries

* Sat Apr 16 2016 Richard Russon <rich@flatcap.org> - NeoMutt-20160416
- Big Bugfix Release
- Bug Fixes:
  - Fix crash caused by sidebar_folder_indent
  - Allow the user to change mailboxes again
  - Correct sidebar's messages counts
  - Only sort the sidebar if we're asked to
  - Fix refresh of pager when toggling the sidebar
  - Compose mode: make messages respect the TITLE_FMT
  - Conditional include if sys/syscall.h
  - Build fix for old compilers
  - Try harder to keep track of the open mailbox
- Changes to Features
  - Allow sidebar_divider_char to be longer
    (it was limited to one character)
  - Ignore case when sorting the sidebar alphabetically
- Other Changes
  - Numerous small tweaks to the docs
  - Lots of minor code tidy-ups
  - Enabling NotMuch now forcibly enables Sidebar
    (it is dependent on it, for now)
  - A couple of bug fixes from mutt/stable

* Mon Apr 04 2016 Richard Russon <rich@flatcap.org> - NeoMutt-20160404
- Update for Mutt-1.6.0
- No other changes in this release

* Mon Mar 28 2016 Richard Russon <rich@flatcap.org> - NeoMutt-20160328
- New Features
  - skip-quoted          - skip quoted text
  - limit-current-thread - limit index view to current thread
- Sidebar Intro - A Gentle Introduction to the Sidebar (with pictures).

* Sun Mar 20 2016 Richard Russon <rich@flatcap.org> - NeoMutt-20160320
- Numerous small bugfixes
- TravisCI integration

* Thu Mar 17 2016 Richard Russon <rich@flatcap.org> - NeoMutt-20160317
- New Features
  - notmuch - email search support
  - ifdef   - improvements

* Mon Mar 07 2016 Richard Russon <rich@flatcap.org> - NeoMutt-20160307
- First NeoMutt release
- List of Features:
  - bug-fixes    - various bug fixes
  - cond-date    - use rules to choose date format
  - fmemopen     - use memory buffers instead of files
  - ifdef        - conditional config options
  - index-color  - theme the email index
  - initials     - expando for author's initials
  - nested-if    - allow deeply nested conditions
  - progress     - show a visual progress bar
  - quasi-delete - mark emails to be hidden
  - sidebar      - overview of mailboxes
  - status-color - theming the status bar
  - tls-sni      - negotiate for a certificate
  - trash        - move 'deleted' emails to a trash bin

