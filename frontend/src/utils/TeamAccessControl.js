/**
 * Security Team Access Control
 * Only allows 4 designated team members to access protected features
 */

const TEAM_MEMBERS = [
  'vineet@depin.local',
  'priyanshu@depin.local',
  'mohit@depin.local',
  'prateek@depin.local'
];

export class TeamAccessControl {
  static isTeamMember(email) {
    if (!email) return false;
    const normalizedEmail = email.toLowerCase().trim();
    return TEAM_MEMBERS.some(member => 
      normalizedEmail.includes(member.split('@')[0]) || 
      normalizedEmail === member
    );
  }

  static canAccessSecurityPage(email) {
    return this.isTeamMember(email);
  }

  static getTeamStatus() {
    return {
      totalMembers: TEAM_MEMBERS.length,
      members: TEAM_MEMBERS,
    };
  }

  static logAccessAttempt(email, allowed, page) {
    const timestamp = new Date().toISOString();
    const log = {
      timestamp,
      email,
      allowed,
      page,
      action: allowed ? 'ACCESS_GRANTED' : 'ACCESS_DENIED'
    };
    
    // Store in localStorage for audit trail (up to 50 entries)
    try {
      let auditLog = JSON.parse(localStorage.getItem('security_audit_log') || '[]');
      auditLog.push(log);
      auditLog = auditLog.slice(-50); // Keep last 50
      localStorage.setItem('security_audit_log', JSON.stringify(auditLog));
    } catch {}

    console.log(`[Security] ${log.action}: ${email} trying to access ${page}`);
    return log;
  }

  static getAuditLog() {
    try {
      return JSON.parse(localStorage.getItem('security_audit_log') || '[]');
    } catch {
      return [];
    }
  }
}

export default TeamAccessControl;
