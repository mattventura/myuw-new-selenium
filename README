Setting up the testing environment:
	Install myuw
	Clone this repository
	Configure desired settings in testconfig.py

Running tests:
	Recommended prep:
		1. Start an xvfb or Xephyr instance
		2. Set $DISPLAY accordingly

	1. Start myuw server
	2. Run main.py to start tests

	Options for main.py:
		With no arguments, test everything possible
		--user: restrict testing to one user (e.g. --user javerage)
		--single: specify individual test cases in user:date format (e.g. --single javerage:2013-4-4 jinter:2013-5-5). 
			Reports results in JSON. Used internally. 
		--debug: run scratch code defined in main.py
		--dump-dates: show what users and dates would be tested with no arguments

Results reporting:
	main.py will report its results in the following format:

For user javerage:
	On date 2013-1-20:
		Didn't find expected card ThriveCard
		Found unexpected card app_acal
		Summer Registration card in wrong position
	On date 2013-4-1:
		The following cards did not finish loading: ThriveCard
For user jinter:
	...

What happens when testing:
	
	The primary instance of the program figures out what user/date pairs need to be tested based on the supplied arguments. 
	Then, it divides the pairs across N instances as configured in testconfig. 
	Each instance uses one Webdriver, which is why xvfb or Xephyr is highly recommended, as you wouldn't want 9 web browsers clogging up your workspace. 

	An instance will iterate through its user/date combinations, doing the following:
		1. Override user (if not already that user). 
		2. Override date (if not already that date). 
		3. Go to landing page. 
		4. Parse landing page (find card elements, turn them into instances of cards as defined in myuwtesting.cards). 
		5. Compare these card instances to the expected cards as defined in myuwtesting.expected.
			#5 includes:
			a. Presence of the cards themselves (ensure no missing or unexpected cards)
			b. Whether or not the card should be an error card
			c. Cards that are hung/failed to load in time (10 seconds) will be flagged
			d. If the card class's code supports it, compare the actual content of the card. 
		6. Assemble results into one dictionary, report it back to the master process. 

	Then, the main process merges the results reported by each subprocess, and reports them in the format described above. 

How expected results and behavior are specified:

	Expected results for each user are defined in myuwtesting.expected. 
	Each user has a list of cards associated with them. Multiple cards of the same type/name can be specified by a user, as long as the dates for which they are expected do not overlap. 
	Show/hide is determined by the card classes themselves, but can be further refined by card proxy classes. 
	The test mechanism will use the show/hide behavior to automatically determine what dates should be tested. Cards can override this, in order to specify additional dates which are significant enough to warrant testing (such as dates where the content of the card will change, e.g. Thrive). 

Currently tested card content:

	All cards have the presence/lack thereof of the card tested, even if it is not listed here. 
	Email link: Gmail vs Outlook. 
	HFSCard: Balances, Add Funds URL. 
	EmpFacStudentCard: Presence of student employee section, presence of instructor section. 
	FutureQuarterCard: Which quarters appear, and how many credits and sections for each quarter. 
	SummerEFSCard: Which sections of the card appear (Critical summer info, EFS info)
	GradeCard: Each class's grade (or lack thereof) for every quarter. 
	RegStatusCard: Number of holds. 
	SummerRegStatusCard(A|1): Position of the card (A vs 1), number of holds. 
	CriticalInfoCard: Presence/lack of each of the three sections on the card. 
	VisualScheduleCard: List of classes on the VS
	FinalExamCard: Content not tested
	CourseCards: Content not tested
	NoCourseCard: Appears in place of VS, FE, etc. No content to test. 
	LibraryCard: Content not tested
	TextbookCard: Content not tested
	GradCommitteeCard: All content on the card other than the title is tested
	GradStatusCard: All content is tested, including date-based show/hide. 
	ThriveCard: Just title, but looking to expand it. 

	More presence-only-test cards:
		TuitionCard
		EventsCard
		PCEBanner
		app_notices
		app_acal
		ToRegisterCard
		InternationalStuCard

Currently tested users:
	javerage
	jbothell
	jerror
	jinter
	botgrad
	seagrad
	none
